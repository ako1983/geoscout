#!/usr/bin/env python3
"""
GeoScout Mineral Exploration Agent
Uses LangGraph to create an intelligent agent that analyzes satellite data
for mineral exploration using Claude via Anthropic API
"""

import os
import json
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
import rasterio
import numpy as np
from pathlib import Path


# Site information
SITES = {
    'mountain_pass_ca': {
        'name': 'Mountain Pass, CA',
        'lon': -115.5408,
        'lat': 35.4881,
        'minerals': ['Rare Earth Elements', 'Carbonatites'],
        'geology': 'Carbonatite complex with REE mineralization'
    },
    'bingham_canyon_ut': {
        'name': 'Bingham Canyon, UT',
        'lon': -112.1500,
        'lat': 40.5231,
        'minerals': ['Copper', 'Molybdenum', 'Gold', 'Silver'],
        'geology': 'Porphyry copper deposit with extensive alteration zones'
    },
    'bokan_mountain_ak': {
        'name': 'Bokan Mountain, AK',
        'lon': -132.1583,
        'lat': 54.8867,
        'minerals': ['Rare Earth Elements', 'Uranium'],
        'geology': 'Peralkaline granite with REE and U mineralization'
    }
}


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_site: str
    analysis_results: dict


def get_data_path(site_key: str) -> Path:
    """Get path to site GeoTIFF file"""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / f"{site_key}_sentinel2.tif"


@tool
def get_available_sites() -> str:
    """
    Get information about all available mineral exploration sites.

    Returns:
        JSON string with site details including name, coordinates, target minerals, and geology
    """
    sites_info = []
    for key, info in SITES.items():
        data_path = get_data_path(key)
        sites_info.append({
            'key': key,
            'name': info['name'],
            'coordinates': {'lat': info['lat'], 'lon': info['lon']},
            'minerals': info['minerals'],
            'geology': info['geology'],
            'data_available': data_path.exists()
        })

    return json.dumps(sites_info, indent=2)


@tool
def calculate_mineral_indices(site_key: str) -> str:
    """
    Calculate spectral mineral indices for a site using Sentinel-2 bands.

    Calculates:
    - Iron oxide index (Red/Blue): High values indicate oxidized iron minerals
    - Ferrous index (SWIR1/NIR): High values indicate iron-bearing minerals
    - Clay index (SWIR1/SWIR2): High values indicate clay alteration
    - NDVI: Vegetation cover (can mask mineral signatures)

    Args:
        site_key: Site identifier (mountain_pass_ca, bingham_canyon_ut, or bokan_mountain_ak)

    Returns:
        JSON string with calculated indices and statistics
    """
    if site_key not in SITES:
        return json.dumps({
            'error': f"Unknown site: {site_key}",
            'available_sites': list(SITES.keys())
        })

    data_path = get_data_path(site_key)
    if not data_path.exists():
        return json.dumps({
            'error': f"No data available for {site_key}. Download imagery first.",
            'site': site_key
        })

    try:
        # Read bands
        with rasterio.open(data_path) as src:
            bands = src.read().astype(float)  # Shape: (6, height, width)

        # Extract individual bands
        b2 = bands[0]  # Blue
        b3 = bands[1]  # Green
        b4 = bands[2]  # Red
        b8 = bands[3]  # NIR
        b11 = bands[4] # SWIR1
        b12 = bands[5] # SWIR2

        epsilon = 1e-10

        # Calculate indices
        indices = {
            'iron_oxide': np.divide(b4, b2 + epsilon),
            'ferrous': np.divide(b11, b8 + epsilon),
            'clay': np.divide(b11, b12 + epsilon),
            'ndvi': np.divide(b8 - b4, b8 + b4 + epsilon)
        }

        # Calculate statistics for each index
        results = {'site': SITES[site_key]['name'], 'indices': {}}

        for idx_name, idx_data in indices.items():
            valid = ~np.isnan(idx_data) & ~np.isinf(idx_data)
            stats = {
                'mean': float(np.mean(idx_data[valid])),
                'std': float(np.std(idx_data[valid])),
                'min': float(np.min(idx_data[valid])),
                'max': float(np.max(idx_data[valid])),
                'p25': float(np.percentile(idx_data[valid], 25)),
                'p50': float(np.percentile(idx_data[valid], 50)),
                'p75': float(np.percentile(idx_data[valid], 75))
            }
            results['indices'][idx_name] = stats

        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({'error': f"Failed to process {site_key}: {str(e)}"})


@tool
def get_spectral_signature(site_key: str, percentile: int = 90) -> str:
    """
    Extract spectral signature for bright pixels at a site (potential mineral targets).

    Args:
        site_key: Site identifier
        percentile: Percentile threshold for selecting bright pixels (default: 90)

    Returns:
        JSON string with mean spectral values for each band
    """
    if site_key not in SITES:
        return json.dumps({'error': f"Unknown site: {site_key}"})

    data_path = get_data_path(site_key)
    if not data_path.exists():
        return json.dumps({'error': f"No data available for {site_key}"})

    try:
        with rasterio.open(data_path) as src:
            bands = src.read().astype(float)

        # Calculate overall brightness (sum of all bands)
        brightness = np.sum(bands, axis=0)
        threshold = np.percentile(brightness, percentile)

        # Select pixels above threshold
        bright_mask = brightness >= threshold

        # Extract spectral signature
        band_names = ['B2_Blue', 'B3_Green', 'B4_Red', 'B8_NIR', 'B11_SWIR1', 'B12_SWIR2']
        signature = {}

        for i, name in enumerate(band_names):
            signature[name] = {
                'mean': float(np.mean(bands[i][bright_mask])),
                'std': float(np.std(bands[i][bright_mask])),
                'count': int(np.sum(bright_mask))
            }

        result = {
            'site': SITES[site_key]['name'],
            'percentile': percentile,
            'spectral_signature': signature
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({'error': f"Failed to extract signature: {str(e)}"})


@tool
def analyze_alteration_zones(site_key: str) -> str:
    """
    Identify and analyze hydrothermal alteration zones using spectral indices.

    Alteration zones are key indicators of mineral deposits. This tool identifies:
    - Iron oxide zones (gossans, oxidized minerals)
    - Clay alteration zones (phyllic/argillic alteration)
    - Ferrous mineral zones

    Args:
        site_key: Site identifier

    Returns:
        JSON string with alteration zone analysis and recommendations
    """
    if site_key not in SITES:
        return json.dumps({'error': f"Unknown site: {site_key}"})

    data_path = get_data_path(site_key)
    if not data_path.exists():
        return json.dumps({'error': f"No data available for {site_key}"})

    try:
        with rasterio.open(data_path) as src:
            bands = src.read().astype(float)

        b2, b3, b4, b8, b11, b12 = bands
        epsilon = 1e-10

        # Calculate indices
        iron_oxide = np.divide(b4, b2 + epsilon)
        clay = np.divide(b11, b12 + epsilon)
        ferrous = np.divide(b11, b8 + epsilon)

        # Define thresholds based on typical values
        iron_oxide_high = iron_oxide > np.percentile(iron_oxide, 75)
        clay_high = clay > np.percentile(clay, 75)
        ferrous_high = ferrous > np.percentile(ferrous, 75)

        # Calculate areas
        total_pixels = iron_oxide.size
        alteration_zones = {
            'iron_oxide_zone': {
                'percent_area': float(np.sum(iron_oxide_high) / total_pixels * 100),
                'mean_value': float(np.mean(iron_oxide[iron_oxide_high])),
                'interpretation': 'Oxidized minerals, possible gossans'
            },
            'clay_alteration_zone': {
                'percent_area': float(np.sum(clay_high) / total_pixels * 100),
                'mean_value': float(np.mean(clay[clay_high])),
                'interpretation': 'Hydrothermal alteration, phyllic/argillic zones'
            },
            'ferrous_zone': {
                'percent_area': float(np.sum(ferrous_high) / total_pixels * 100),
                'mean_value': float(np.mean(ferrous[ferrous_high])),
                'interpretation': 'Iron-bearing minerals'
            }
        }

        # Identify overlap zones (multiple alteration types)
        overlap = iron_oxide_high & clay_high
        overlap_percent = float(np.sum(overlap) / total_pixels * 100)

        site_info = SITES[site_key]
        result = {
            'site': site_info['name'],
            'target_minerals': site_info['minerals'],
            'alteration_zones': alteration_zones,
            'overlap_zone_percent': overlap_percent,
            'recommendations': generate_recommendations(
                site_key, alteration_zones, overlap_percent
            )
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({'error': f"Failed to analyze alteration: {str(e)}"})


def generate_recommendations(site_key: str, alteration_zones: dict, overlap: float) -> list[str]:
    """Generate exploration recommendations based on alteration analysis"""
    recommendations = []
    site_info = SITES[site_key]

    # Iron oxide zones
    if alteration_zones['iron_oxide_zone']['percent_area'] > 10:
        recommendations.append(
            "Significant iron oxide zones detected - prioritize these areas for gossan exploration"
        )

    # Clay alteration
    if alteration_zones['clay_alteration_zone']['percent_area'] > 15:
        recommendations.append(
            f"Extensive hydrothermal alteration detected - "
            f"consistent with {', '.join(site_info['minerals'])} mineralization"
        )

    # Overlap zones
    if overlap > 5:
        recommendations.append(
            f"Multi-alteration overlap zones cover {overlap:.1f}% - "
            "these are high-priority targets for detailed ground surveys"
        )

    # Site-specific recommendations
    if site_key == 'mountain_pass_ca':
        recommendations.append(
            "For REE exploration: focus on carbonatite contacts and areas with anomalous SWIR signatures"
        )
    elif site_key == 'bingham_canyon_ut':
        recommendations.append(
            "Porphyry deposit: look for zoned alteration patterns (potassic core, phyllic halo)"
        )
    elif site_key == 'bokan_mountain_ak':
        recommendations.append(
            "Peralkaline system: prioritize areas with strong iron oxide and REE signatures"
        )

    if not recommendations:
        recommendations.append("Conduct detailed ground surveys to validate spectral anomalies")

    return recommendations


# Create tools list
tools = [
    get_available_sites,
    calculate_mineral_indices,
    get_spectral_signature,
    analyze_alteration_zones
]


def create_agent(api_key: str = None) -> StateGraph:
    """
    Create a LangGraph agent for mineral exploration analysis.

    Args:
        api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)

    Returns:
        Compiled LangGraph StateGraph
    """
    # Initialize Claude
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        temperature=0
    ).bind_tools(tools)

    # Define agent node
    def call_model(state: AgentState):
        messages = state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}

    # Create tool node
    tool_node = ToolNode(tools)

    # Define conditional edge logic
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM makes a tool call, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        # Otherwise end
        return END

    # Build graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    # Compile
    return workflow.compile()


def run_analysis(query: str, api_key: str = None) -> dict:
    """
    Run mineral exploration analysis with the agent.

    Args:
        query: User query about mineral exploration
        api_key: Anthropic API key

    Returns:
        Dictionary with analysis results
    """
    agent = create_agent(api_key)

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "current_site": "",
        "analysis_results": {}
    }

    # Run agent
    result = agent.invoke(initial_state)

    # Extract final response
    messages = result["messages"]
    final_message = messages[-1]

    return {
        "response": final_message.content,
        "messages": [
            {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
            for m in messages
        ]
    }


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mineral_agent.py 'Your query here'")
        print("\nExample queries:")
        print("  - 'What sites are available for analysis?'")
        print("  - 'Analyze Mountain Pass, CA for rare earth minerals'")
        print("  - 'Calculate mineral indices for Bingham Canyon'")
        sys.exit(1)

    query = sys.argv[1]
    result = run_analysis(query)
    print("\n" + "="*60)
    print("GEOSCOUT MINERAL EXPLORATION AGENT")
    print("="*60)
    print(f"\nQuery: {query}\n")
    print(result["response"])
    print("\n" + "="*60)
