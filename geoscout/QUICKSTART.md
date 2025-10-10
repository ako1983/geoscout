# GeoScout Quick Start Guide

## 🎉 Setup Complete!

All three Sentinel-2 satellite scenes have been successfully downloaded:

- ✅ **Mountain Pass, CA** - 7.7 MB (1223x1002 pixels)
- ✅ **Bingham Canyon, UT** - 6.3 MB (1310x1002 pixels)
- ✅ **Bokan Mountain, AK** - 589 KB (1732x1002 pixels)

All scenes are from 2024 with 0% cloud cover!

## 🚀 Launch the Application

### Option 1: Streamlit Web UI (Recommended)

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"

# Launch the app
cd geoscout/ui
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Option 2: Command Line Agent

```bash
export ANTHROPIC_API_KEY="your-key-here"

cd geoscout/agent
python mineral_agent.py "Calculate mineral indices for Mountain Pass, CA"
```

### Option 3: MCP Server (Advanced)

```bash
cd geoscout/mcp_server
python server.py
```

## 📊 What You Can Do

### In the Streamlit UI:

1. **Map View** - See all sites on an interactive map
2. **Mineral Indices** - Calculate and visualize:
   - Iron Oxide Index (Red/Blue)
   - Clay Alteration Index (SWIR1/SWIR2)
   - Ferrous Minerals Index (SWIR1/NIR)
   - NDVI (Vegetation)

3. **Alteration Zones** - Identify hydrothermal alteration:
   - Iron oxide zones (gossans)
   - Clay alteration zones (phyllic/argillic)
   - Ferrous mineral zones
   - Multi-alteration overlap zones

4. **AI Chat** - Ask questions like:
   - "What mineral indices should I calculate for Bingham Canyon?"
   - "Analyze the alteration patterns at Mountain Pass"
   - "Which site shows the strongest iron oxide signature?"
   - "Recommend priority targets for ground surveys"

## 🔬 Example Analysis Workflow

### 1. Initial Reconnaissance
```
Go to Map View → Select site → Check data availability
```

### 2. Spectral Analysis
```
Go to Mineral Indices → Select site → Click "Calculate Indices"
Review the bar charts and statistics
```

### 3. Target Identification
```
Go to Alteration Zones → Select site → Click "Analyze Alteration"
Review coverage percentages and recommendations
```

### 4. AI Consultation
```
Go to AI Chat → Ask: "Based on the spectral data, where should I focus ground surveys at [site name]?"
```

## 📝 Site Information

### Mountain Pass, CA
- **Deposit Type:** Carbonatite REE
- **Date:** 2024-08-27
- **Cloud Cover:** 0.0%
- **Target Minerals:** Rare Earth Elements, Bastnäsite

### Bingham Canyon, UT
- **Deposit Type:** Porphyry Cu-Mo-Au-Ag
- **Date:** 2024-09-06
- **Cloud Cover:** 0.0%
- **Target Minerals:** Copper, Molybdenum, Gold, Silver

### Bokan Mountain, AK
- **Deposit Type:** Peralkaline Granite REE-U
- **Date:** 2024-03-20
- **Cloud Cover:** 0.0%
- **Target Minerals:** Rare Earth Elements, Uranium

## 🛠️ Troubleshooting

### "API key not set"
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "Module not found"
```bash
# Make sure you're in the right directory
cd geoscout/ui  # for Streamlit
# or
cd geoscout/agent  # for CLI agent
```

### "No data available"
The data is already downloaded! Files are in `geoscout/data/`

## 🎓 Learn More

See the full README.md for:
- Detailed architecture
- MCP server tools
- Mineral index interpretation
- Technical specifications
- API reference

## 💡 Tips

1. **Start with Map View** to orient yourself
2. **Calculate indices** for all three sites to compare
3. **Use AI Chat** to get interpretation help
4. **Look for overlap zones** - these are high-priority targets
5. **Compare iron oxide and clay indices** - both high = potential deposit

Enjoy exploring! 🛰️
