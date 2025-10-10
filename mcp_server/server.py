#!/usr/bin/env python3
"""
GeoScout MCP Server - Provides satellite data access tools
Exposes Sentinel-2 imagery and mineral index calculations via MCP protocol
"""

import os
import json
from pathlib import Path
from typing import Any, Sequence
import rasterio
import numpy as np
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, Field
import mcp.server.stdio


# Site information
SITES = {
    'mountain_pass_ca': {
        'name': 'Mountain Pass, CA',
        'lon': -115.5408,
        'lat': 35.4881,
        'minerals': ['Rare Earth Elements', 'Carbonatites']
    },
    'bingham_canyon_ut': {
        'name': 'Bingham Canyon, UT',
        'lon': -112.1500,
        'lat': 40.5231,
        'minerals': ['Copper', 'Molybdenum', 'Gold', 'Silver']
    },
    'bokan_mountain_ak': {
        'name': 'Bokan Mountain, AK',
        'lon': -132.1583,
        'lat': 54.8867,
        'minerals': ['Rare Earth Elements', 'Uranium']
    }
}

# Band indices for Sentinel-2
BAND_INDICES = {
    'B2': 0,  # Blue
    'B3': 1,  # Green
    'B4': 2,  # Red
    'B8': 3,  # NIR
    'B11': 4, # SWIR1
    'B12': 5  # SWIR2
}


class GetSitesInput(BaseModel):
    """Input for get_sites tool"""
    pass


class GetImageInput(BaseModel):
    """Input for get_image tool"""
    site_key: str = Field(description="Site key (mountain_pass_ca, bingham_canyon_ut, or bokan_mountain_ak)")
    visualization: str = Field(
        default="rgb",
        description="Visualization type: rgb, false_color, iron_oxide, ferrous, clay"
    )


class CalculateIndexInput(BaseModel):
    """Input for calculate_mineral_index tool"""
    site_key: str = Field(description="Site key")
    index_type: str = Field(description="Index type: iron_oxide, ferrous, clay, vegetation")


# Initialize MCP server
app = Server("geoscout")


def get_data_path(site_key: str) -> Path:
    """Get path to site GeoTIFF file"""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / f"{site_key}_sentinel2.tif"


def read_bands(site_key: str) -> tuple[np.ndarray, dict]:
    """Read all bands from a GeoTIFF file"""
    file_path = get_data_path(site_key)

    if not file_path.exists():
        raise FileNotFoundError(f"No data found for {site_key}. Run download_sentinel2.py first.")

    with rasterio.open(file_path) as src:
        # Read all bands
        bands = src.read()  # Shape: (6, height, width)
        metadata = {
            'bounds': src.bounds,
            'crs': str(src.crs),
            'transform': src.transform,
            'width': src.width,
            'height': src.height
        }

    return bands, metadata


def calculate_mineral_index(bands: np.ndarray, index_type: str) -> np.ndarray:
    """
    Calculate mineral spectral indices from Sentinel-2 bands

    Args:
        bands: Array with shape (6, height, width) containing B2,B3,B4,B8,B11,B12
        index_type: Type of index to calculate

    Returns:
        2D array with calculated index values
    """
    # Extract bands
    b2 = bands[0].astype(float)  # Blue
    b3 = bands[1].astype(float)  # Green
    b4 = bands[2].astype(float)  # Red
    b8 = bands[3].astype(float)  # NIR
    b11 = bands[4].astype(float) # SWIR1
    b12 = bands[5].astype(float) # SWIR2

    # Avoid division by zero
    epsilon = 1e-10

    if index_type == "iron_oxide":
        # Iron oxide index: Red/Blue
        index = np.divide(b4, b2 + epsilon)

    elif index_type == "ferrous":
        # Ferrous minerals: SWIR1/NIR
        index = np.divide(b11, b8 + epsilon)

    elif index_type == "clay":
        # Clay minerals: SWIR1/SWIR2
        index = np.divide(b11, b12 + epsilon)

    elif index_type == "vegetation":
        # NDVI: (NIR - Red) / (NIR + Red)
        index = np.divide(b8 - b4, b8 + b4 + epsilon)

    else:
        raise ValueError(f"Unknown index type: {index_type}")

    return index


def create_rgb_visualization(bands: np.ndarray, band_indices: list[int]) -> np.ndarray:
    """
    Create RGB visualization from selected bands

    Args:
        bands: Full band array
        band_indices: List of 3 band indices to use for RGB

    Returns:
        RGB array with shape (height, width, 3) normalized to 0-255
    """
    rgb = np.stack([bands[i] for i in band_indices], axis=-1)

    # Normalize to 0-255 (simple percentile stretch)
    p2, p98 = np.percentile(rgb, (2, 98))
    rgb = np.clip((rgb - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)

    return rgb


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="get_sites",
            description="Get list of all available mineral exploration sites with their coordinates and mineral types",
            inputSchema=GetSitesInput.model_json_schema()
        ),
        Tool(
            name="get_image",
            description="Get satellite imagery for a site with specified visualization (rgb, false_color, iron_oxide, ferrous, clay)",
            inputSchema=GetImageInput.model_json_schema()
        ),
        Tool(
            name="calculate_mineral_index",
            description="Calculate spectral mineral index for a site (iron_oxide, ferrous, clay, vegetation)",
            inputSchema=CalculateIndexInput.model_json_schema()
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""

    if name == "get_sites":
        # Return site information
        sites_info = []
        for key, info in SITES.items():
            data_path = get_data_path(key)
            sites_info.append({
                'key': key,
                'name': info['name'],
                'coordinates': {'lat': info['lat'], 'lon': info['lon']},
                'minerals': info['minerals'],
                'data_available': data_path.exists()
            })

        return [TextContent(
            type="text",
            text=json.dumps(sites_info, indent=2)
        )]

    elif name == "get_image":
        site_key = arguments['site_key']
        visualization = arguments.get('visualization', 'rgb')

        if site_key not in SITES:
            return [TextContent(
                type="text",
                text=f"Error: Unknown site key '{site_key}'. Available: {', '.join(SITES.keys())}"
            )]

        try:
            bands, metadata = read_bands(site_key)

            # Create visualization based on type
            if visualization == "rgb":
                # Natural color: Red, Green, Blue
                rgb = create_rgb_visualization(bands, [2, 1, 0])
                description = "Natural color (RGB)"

            elif visualization == "false_color":
                # False color: NIR, Red, Green
                rgb = create_rgb_visualization(bands, [3, 2, 1])
                description = "False color infrared (NIR-R-G)"

            elif visualization == "iron_oxide":
                # Iron oxide composite: SWIR2, SWIR1, Red
                rgb = create_rgb_visualization(bands, [5, 4, 2])
                description = "Iron oxide composite (SWIR2-SWIR1-Red)"

            elif visualization == "ferrous":
                # Ferrous minerals: SWIR1, NIR, Red
                rgb = create_rgb_visualization(bands, [4, 3, 2])
                description = "Ferrous minerals composite (SWIR1-NIR-Red)"

            elif visualization == "clay":
                # Clay minerals: SWIR2, SWIR1, Blue
                rgb = create_rgb_visualization(bands, [5, 4, 0])
                description = "Clay minerals composite (SWIR2-SWIR1-Blue)"

            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown visualization '{visualization}'"
                )]

            site_info = SITES[site_key]
            result_text = f"""Site: {site_info['name']}
Visualization: {description}
Coordinates: {site_info['lat']:.4f}°N, {site_info['lon']:.4f}°W
Minerals: {', '.join(site_info['minerals'])}
Image size: {metadata['width']}x{metadata['height']} pixels
CRS: {metadata['crs']}"""

            return [TextContent(type="text", text=result_text)]

        except FileNotFoundError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error processing image: {str(e)}")]

    elif name == "calculate_mineral_index":
        site_key = arguments['site_key']
        index_type = arguments['index_type']

        if site_key not in SITES:
            return [TextContent(
                type="text",
                text=f"Error: Unknown site key '{site_key}'"
            )]

        try:
            bands, metadata = read_bands(site_key)
            index = calculate_mineral_index(bands, index_type)

            # Calculate statistics
            valid_pixels = ~np.isnan(index) & ~np.isinf(index)
            stats = {
                'mean': float(np.mean(index[valid_pixels])),
                'std': float(np.std(index[valid_pixels])),
                'min': float(np.min(index[valid_pixels])),
                'max': float(np.max(index[valid_pixels])),
                'percentile_25': float(np.percentile(index[valid_pixels], 25)),
                'percentile_50': float(np.percentile(index[valid_pixels], 50)),
                'percentile_75': float(np.percentile(index[valid_pixels], 75))
            }

            site_info = SITES[site_key]
            result = {
                'site': site_info['name'],
                'index_type': index_type,
                'statistics': stats,
                'interpretation': get_index_interpretation(index_type, stats)
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        except FileNotFoundError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error calculating index: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def get_index_interpretation(index_type: str, stats: dict) -> str:
    """Provide interpretation of mineral index results"""
    mean = stats['mean']

    if index_type == "iron_oxide":
        if mean > 1.5:
            return "High iron oxide presence - strong potential for oxidized minerals"
        elif mean > 1.2:
            return "Moderate iron oxide presence - some oxidation visible"
        else:
            return "Low iron oxide presence - limited oxidation"

    elif index_type == "ferrous":
        if mean > 1.1:
            return "High ferrous mineral presence - likely iron-bearing minerals"
        elif mean > 0.9:
            return "Moderate ferrous mineral presence"
        else:
            return "Low ferrous mineral presence"

    elif index_type == "clay":
        if mean > 1.2:
            return "High clay/alteration - strong hydrothermal alteration signature"
        elif mean > 1.0:
            return "Moderate clay/alteration - some alteration present"
        else:
            return "Low clay/alteration"

    elif index_type == "vegetation":
        if mean > 0.5:
            return "High vegetation cover - may obscure mineral signatures"
        elif mean > 0.3:
            return "Moderate vegetation cover"
        else:
            return "Low vegetation - good for mineral mapping"

    return "No interpretation available"


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
