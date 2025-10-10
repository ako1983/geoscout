
🎯 The Problem

* $8 trillion in critical minerals needed by 2050
* US imports 80% of rare earths from China - national security risk
* Billions of satellite images archived but underutilized
* Traditional mineral exploration: slow, expensive, risky


💡 Our Solution: GeoScout AI
AI-powered mineral exploration platform that unlocks dormant Earth observation data using:

* Real satellite imagery (Sentinel-2, 10m resolution)
* MCP architecture (Model Context Protocol from Anthropic)
* Claude AI reasoning for geological interpretation
* LangGraph agents for intelligent analysis


🏗️ Architecture
Satellite Data (Sentinel-2) 
    ↓
MCP Server (exposes data as queryable tools)
    ↓
LangGraph Agent (orchestrates analysis)
    ↓
Claude AI (geological reasoning)
    ↓
Streamlit UI (interactive exploration)

🛰️ Live Demo Sites

* Mountain Pass, CA - Rare Earth Elements (carbonatite, 15% of global supply)
* Bingham Canyon, UT - Copper-Molybdenum (largest porphyry deposit)
* Bokan Mountain, AK - REE + Uranium (peralkaline granite)

All with 2024 imagery, 0% cloud cover

🔬 What It Does
Spectral Mineral Indices:

* Iron Oxide Index (Red/Blue ratio) → Oxidized minerals, gossans
* Clay Alteration Index (SWIR bands) → Hydrothermal alteration zones
* Ferrous Index → Iron-bearing minerals
* NDVI → Vegetation masking

AI Capabilities:

* Natural language queries about mineral potential
* Automated spectral analysis
* Exploration target recommendations
* Multi-site comparative analysis


🚀 Why It Wins
Technical Innovation:

✅ First geospatial application of MCP protocol
✅ Real satellite data, not mock/API wrapper
✅ Production-quality code (2,197 lines, fully functional)
✅ Secure data serving (MCP tool-level authentication)

Strategic Impact:

✅ Unlocks billions in archived satellite data
✅ Addresses critical mineral supply chain security
✅ Scalable to global coverage (any satellite sensor)
✅ Reduces exploration costs and timelines

Built in 3 hours. Cost: $2.28

📊 Key Metrics

* 3 sites analyzed with real 2024 Sentinel-2 data
* 6 spectral bands per scene (Blue, Green, Red, NIR, SWIR1, SWIR2)
* 30m spatial resolution (10m for visible/NIR)
* 4 specialized tools in MCP server
* Claude Sonnet 4 for geological reasoning


🎓 The Vision
* Today: 3 sites, Sentinel-2 data
* Tomorrow: Global coverage, multi-sensor fusion
* Future: Real-time mineral discovery at planetary scale
* Transform Earth observation from passive archive to active intelligence.

Built with Claude Code + Anthropic Claude AI
Team: ClaAko (Claude + Ako) + Claude Code
GitHub: https://github.com/ako1983/geoscout