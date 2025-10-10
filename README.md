# GeoScout 🛰️

AI-powered mineral exploration platform using Sentinel-2 satellite imagery, LangGraph agents, and Claude AI.

## Overview

GeoScout analyzes satellite imagery for three major mineral exploration sites:

1. **Mountain Pass, CA** - Rare Earth Elements (REE) in carbonatite
2. **Bingham Canyon, UT** - Porphyry copper-molybdenum-gold-silver deposit
3. **Bokan Mountain, AK** - REE and uranium in peralkaline granite

## Features

- 📡 **Satellite Data Access** - MCP server for Sentinel-2 imagery
- 🤖 **AI Agent** - LangGraph agent powered by Claude for intelligent analysis
- 📊 **Mineral Indices** - Calculate iron oxide, clay, ferrous, and vegetation indices
- 🗺️ **Interactive UI** - Streamlit web app with maps and visualizations
- 🔬 **Alteration Analysis** - Identify hydrothermal alteration zones

## Architecture

```
geoscout/
├── mcp_server/
│   └── server.py           # MCP server exposing satellite data tools
├── agent/
│   └── mineral_agent.py    # LangGraph agent with Claude AI
├── ui/
│   └── app.py              # Streamlit web interface
└── data/
    └── (Sentinel-2 GeoTIFF files)
```

## Installation

### 1. Prerequisites

- Python 3.8+
- Anthropic API key (for Claude)
- Google Earth Engine account (for downloading imagery)

### 2. Install Dependencies

```bash
pip install earthengine-api geemap mcp langgraph langchain-anthropic streamlit folium streamlit-folium rasterio
```

### 3. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Step 1: Download Satellite Imagery

First, register your Google Cloud project with Earth Engine:
1. Visit: https://console.cloud.google.com/earth-engine/configuration?project=gen-lang-client-0926459788
2. Register the project for Earth Engine access

Then download imagery:

```bash
python download_sentinel2.py
```

This downloads Sentinel-2 scenes (bands 2,3,4,8,11,12) for all three sites to `geoscout/data/`.

### Step 2: Run the Streamlit UI

```bash
cd geoscout/ui
streamlit run app.py
```

The web interface will open at `http://localhost:8501`

### Step 3: Use the MCP Server (Optional)

The MCP server can be run standalone for programmatic access:

```bash
cd geoscout/mcp_server
python server.py
```

### Step 4: Use the AI Agent (CLI)

Run the agent from command line:

```bash
cd geoscout/agent
python mineral_agent.py "Analyze Mountain Pass, CA for rare earth minerals"
```

## Streamlit UI Features

### 1. Map View
- Interactive map showing all three exploration sites
- Click markers to see site details
- View coordinates, geology, and target minerals

### 2. Mineral Indices
- Calculate spectral indices from Sentinel-2 bands:
  - **Iron Oxide Index** (Red/Blue): Oxidized minerals, gossans
  - **Ferrous Index** (SWIR1/NIR): Iron-bearing minerals
  - **Clay Index** (SWIR1/SWIR2): Hydrothermal alteration
  - **NDVI**: Vegetation cover
- View statistical summaries and visualizations

### 3. Alteration Zones
- Identify hydrothermal alteration zones
- Calculate coverage percentages
- Get exploration recommendations
- Find multi-alteration overlap zones (high priority targets)

### 4. AI Chat
- Ask natural language questions about sites
- Get intelligent analysis from Claude
- Examples:
  - "What mineral indices should I calculate for this site?"
  - "Analyze the alteration patterns at Bingham Canyon"
  - "Compare spectral signatures across different zones"

## MCP Server Tools

The MCP server exposes three tools:

### 1. `get_sites`
Returns information about all available sites with coordinates, minerals, and data availability.

### 2. `get_image`
Get satellite imagery with visualization options:
- `rgb` - Natural color
- `false_color` - NIR-Red-Green composite
- `iron_oxide` - Iron oxide composite
- `ferrous` - Ferrous minerals composite
- `clay` - Clay alteration composite

### 3. `calculate_mineral_index`
Calculate spectral indices:
- `iron_oxide` - Iron oxide minerals
- `ferrous` - Ferrous minerals
- `clay` - Clay alteration
- `vegetation` - NDVI

## LangGraph Agent Tools

The agent has four tools:

1. **`get_available_sites()`** - List all sites with details
2. **`calculate_mineral_indices(site_key)`** - Calculate all indices for a site
3. **`get_spectral_signature(site_key, percentile)`** - Extract bright pixel signatures
4. **`analyze_alteration_zones(site_key)`** - Comprehensive alteration analysis

## Sentinel-2 Bands Used

| Band | Wavelength | Resolution | Purpose |
|------|------------|------------|---------|
| B2   | 490 nm (Blue) | 10m | Iron oxide index, clay minerals |
| B3   | 560 nm (Green) | 10m | Vegetation, RGB visualization |
| B4   | 665 nm (Red) | 10m | Iron oxide, RGB visualization |
| B8   | 842 nm (NIR) | 10m | Vegetation, ferrous minerals |
| B11  | 1610 nm (SWIR1) | 20m | Clay, hydroxyl minerals |
| B12  | 2190 nm (SWIR2) | 20m | Clay, carbonate minerals |

## Mineral Index Interpretation

### Iron Oxide Index (Red/Blue)
- **High (>1.5)**: Strong oxidation, gossans, limonite
- **Moderate (1.2-1.5)**: Some oxidation
- **Low (<1.2)**: Minimal oxidation

### Clay Alteration Index (SWIR1/SWIR2)
- **High (>1.2)**: Strong hydrothermal alteration (phyllic/argillic)
- **Moderate (1.0-1.2)**: Moderate alteration
- **Low (<1.0)**: Minimal alteration

### Ferrous Index (SWIR1/NIR)
- **High (>1.1)**: Iron-bearing minerals (magnetite, pyroxene)
- Useful for mafic/ultramafic complexes

## Example Workflows

### Workflow 1: Initial Site Assessment

```bash
# 1. Download imagery
python download_sentinel2.py

# 2. Launch UI
cd geoscout/ui
streamlit run app.py

# 3. In UI:
#    - View site on map
#    - Calculate mineral indices
#    - Review statistics
```

### Workflow 2: Detailed Exploration Analysis

```bash
# 1. Use AI agent for comprehensive analysis
cd geoscout/agent
python mineral_agent.py "Perform complete exploration analysis for Bingham Canyon including alteration zones and spectral signatures"

# 2. Review results and identify targets
# 3. Use UI to visualize specific indices
```

### Workflow 3: Comparative Analysis

```bash
# Use AI chat in Streamlit UI:
# "Compare iron oxide signatures across all three sites"
# "Which site shows the strongest hydrothermal alteration?"
# "Recommend priority targets for ground surveys"
```

## Troubleshooting

### Earth Engine Registration Error

If you see: `Project is not registered to use Earth Engine`

**Solution:**
1. Visit the registration URL in the error message
2. Register your project for Earth Engine access
3. Wait a few minutes for registration to complete
4. Re-run `download_sentinel2.py`

### Missing Satellite Data

If the UI shows "No data available":

**Solution:**
1. Ensure you've run `download_sentinel2.py` successfully
2. Check that GeoTIFF files exist in `geoscout/data/`
3. Verify files are named: `{site_key}_sentinel2.tif`

### API Key Not Found

If you see warnings about `ANTHROPIC_API_KEY`:

**Solution:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Or enter the key in the Streamlit sidebar.

## Site Details

### Mountain Pass, California
- **Coordinates:** 35.4881°N, 115.5408°W
- **Deposit Type:** Carbonatite-hosted REE
- **Key Minerals:** Bastnäsite (REE-fluorocarbonate)
- **Geology:** Proterozoic carbonatite intrusion
- **Exploration Focus:** Iron oxide + REE signatures

### Bingham Canyon, Utah
- **Coordinates:** 40.5231°N, 112.1500°W
- **Deposit Type:** Porphyry Cu-Mo-Au-Ag
- **Key Minerals:** Chalcopyrite, molybdenite, native gold
- **Geology:** Tertiary quartz monzonite porphyry
- **Exploration Focus:** Zoned alteration (potassic core, phyllic halo)

### Bokan Mountain, Alaska
- **Coordinates:** 54.8867°N, 132.1583°W
- **Deposit Type:** Peralkaline granite-hosted REE-U
- **Key Minerals:** REE minerals, uraninite
- **Geology:** Jurassic peralkaline granite
- **Exploration Focus:** Iron oxide + SWIR anomalies

## Technical Notes

### Data Processing
- All indices use epsilon (1e-10) to avoid division by zero
- Percentile stretching (2-98%) for visualization
- Statistical analysis uses valid pixels only (excludes NaN/Inf)

### Performance
- Image processing is done in-memory with NumPy
- GeoTIFF files are ~50-100MB per site
- Agent responses typically take 2-10 seconds

### Coordinate Systems
- Input coordinates: WGS84 (EPSG:4326)
- GeoTIFF files: WGS84 (EPSG:4326)
- Sentinel-2 native: UTM (converted during download)

## References

- Sentinel-2 Mission: https://sentinel.esa.int/web/sentinel/missions/sentinel-2
- Mineral Indices: https://www.usgs.gov/spectroscopy-lab
- LangGraph: https://langchain-ai.github.io/langgraph/
- MCP Protocol: https://modelcontextprotocol.io/

## License

This project is for educational and research purposes.
Sentinel-2 data courtesy of ESA Copernicus Program.

## Contributing

Contributions welcome! Areas for enhancement:
- Additional mineral indices (ASTER, Landsat)
- Machine learning classification
- Time series analysis
- Export capabilities (KML, shapefile)
- Integration with geological databases

## Contact

Built with Claude Code and Anthropic's Claude AI.
