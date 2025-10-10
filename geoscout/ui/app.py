#!/usr/bin/env python3
"""
GeoScout Streamlit UI
Interactive web application for mineral exploration analysis
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import sys
import os
from pathlib import Path
import json
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.mineral_agent import run_analysis, SITES, get_data_path


# Page config
st.set_page_config(
    page_title="GeoScout - Mineral Exploration",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .site-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def create_map(sites: dict, selected_site: str = None):
    """Create Folium map with site markers"""
    # Center map on US
    m = folium.Map(
        location=[39.8, -98.5],
        zoom_start=4,
        tiles="OpenStreetMap"
    )

    # Add markers for each site
    for key, info in sites.items():
        is_selected = (key == selected_site)
        color = 'red' if is_selected else 'blue'
        icon = 'star' if is_selected else 'info-sign'

        folium.Marker(
            location=[info['lat'], info['lon']],
            popup=f"<b>{info['name']}</b><br>Minerals: {', '.join(info['minerals'])}",
            tooltip=info['name'],
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(m)

    return m


def plot_mineral_indices(indices_data: dict):
    """Plot mineral indices as bar chart"""
    if 'error' in indices_data:
        st.error(indices_data['error'])
        return

    indices = indices_data.get('indices', {})
    if not indices:
        st.warning("No index data available")
        return

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"Mineral Indices - {indices_data['site']}", fontsize=16, fontweight='bold')

    index_names = ['iron_oxide', 'ferrous', 'clay', 'ndvi']
    titles = ['Iron Oxide Index', 'Ferrous Minerals Index', 'Clay Alteration Index', 'NDVI (Vegetation)']
    colors = ['#d62728', '#ff7f0e', '#8c564b', '#2ca02c']

    for ax, idx_name, title, color in zip(axes.flat, index_names, titles, colors):
        if idx_name in indices:
            stats = indices[idx_name]

            # Create box plot style visualization
            ax.barh(['Mean'], [stats['mean']], color=color, alpha=0.7, label='Mean')
            ax.axvline(stats['p50'], color='black', linestyle='--', linewidth=2, label='Median')
            ax.axvline(stats['p25'], color='gray', linestyle=':', linewidth=1)
            ax.axvline(stats['p75'], color='gray', linestyle=':', linewidth=1)

            ax.set_xlabel('Index Value')
            ax.set_title(title, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(axis='x', alpha=0.3)

            # Add text annotation
            ax.text(stats['mean'], 0, f"{stats['mean']:.3f}",
                   ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig)

    # Display statistics table
    st.subheader("Statistical Summary")
    stats_dict = {}
    for idx_name in index_names:
        if idx_name in indices:
            stats = indices[idx_name]
            stats_dict[idx_name] = {
                'Mean': f"{stats['mean']:.3f}",
                'Std Dev': f"{stats['std']:.3f}",
                'Min': f"{stats['min']:.3f}",
                'Max': f"{stats['max']:.3f}",
                '25%': f"{stats['p25']:.3f}",
                'Median': f"{stats['p50']:.3f}",
                '75%': f"{stats['p75']:.3f}"
            }

    st.table(stats_dict)


def display_alteration_analysis(alteration_data: dict):
    """Display alteration zone analysis"""
    if 'error' in alteration_data:
        st.error(alteration_data['error'])
        return

    st.subheader(f"Alteration Analysis - {alteration_data['site']}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Alteration Zones")
        zones = alteration_data['alteration_zones']

        for zone_name, zone_data in zones.items():
            with st.container():
                st.markdown(f"**{zone_name.replace('_', ' ').title()}**")
                st.metric(
                    "Coverage",
                    f"{zone_data['percent_area']:.2f}%",
                    help=zone_data['interpretation']
                )
                st.caption(zone_data['interpretation'])
                st.divider()

    with col2:
        st.markdown("### Key Metrics")
        st.metric(
            "Target Minerals",
            ", ".join(alteration_data['target_minerals'])
        )
        st.metric(
            "Multi-Alteration Overlap",
            f"{alteration_data['overlap_zone_percent']:.2f}%",
            help="Areas with multiple alteration types (high priority)"
        )

    st.markdown("### Recommendations")
    for i, rec in enumerate(alteration_data['recommendations'], 1):
        st.info(f"**{i}.** {rec}")


def main():
    """Main Streamlit application"""

    # Header
    st.markdown('<div class="main-header">🛰️ GeoScout</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">AI-Powered Mineral Exploration using Sentinel-2 Satellite Imagery</div>',
        unsafe_allow_html=True
    )

    # Sidebar
    st.sidebar.title("🔍 Analysis Options")

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.sidebar.warning("⚠️ ANTHROPIC_API_KEY not set")
        api_key = st.sidebar.text_input("Enter Anthropic API Key:", type="password")

    # Site selection
    st.sidebar.subheader("Select Site")
    site_keys = list(SITES.keys())
    site_names = [SITES[key]['name'] for key in site_keys]

    selected_name = st.sidebar.selectbox("Exploration Site:", site_names)
    selected_key = site_keys[site_names.index(selected_name)]
    site_info = SITES[selected_key]

    # Display site info
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Location:** {site_info['lat']:.4f}°N, {abs(site_info['lon']):.4f}°W")
    st.sidebar.markdown(f"**Target Minerals:**")
    for mineral in site_info['minerals']:
        st.sidebar.markdown(f"- {mineral}")

    # Check data availability
    data_path = get_data_path(selected_key)
    data_available = data_path.exists()

    if not data_available:
        st.sidebar.error("❌ Satellite data not downloaded")
        st.sidebar.markdown("Run `python download_sentinel2.py` first")
    else:
        st.sidebar.success("✅ Satellite data available")

    # Analysis options
    st.sidebar.subheader("Analysis Type")
    analysis_type = st.sidebar.radio(
        "Choose analysis:",
        ["Map View", "Mineral Indices", "Alteration Zones", "AI Chat"]
    )

    # Main content area
    if analysis_type == "Map View":
        st.header("📍 Site Locations")

        # Create and display map
        m = create_map(SITES, selected_key)
        st_folium(m, width=1200, height=600)

        # Site details
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="site-card">', unsafe_allow_html=True)
            st.subheader(site_info['name'])
            st.markdown(f"**Coordinates:** {site_info['lat']:.4f}°N, {abs(site_info['lon']):.4f}°W")
            st.markdown(f"**Geology:** {site_info['geology']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="site-card">', unsafe_allow_html=True)
            st.subheader("Target Minerals")
            for mineral in site_info['minerals']:
                st.markdown(f"• {mineral}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="site-card">', unsafe_allow_html=True)
            st.subheader("Data Status")
            if data_available:
                st.success("Satellite imagery available")
                with rasterio.open(data_path) as src:
                    st.markdown(f"**Image size:** {src.width} x {src.height} pixels")
                    st.markdown(f"**Bands:** {src.count}")
            else:
                st.error("No imagery downloaded")
            st.markdown('</div>', unsafe_allow_html=True)

    elif analysis_type == "Mineral Indices":
        st.header("📊 Spectral Mineral Indices")

        if not data_available:
            st.error("No satellite data available. Please download imagery first.")
            return

        if st.button("Calculate Indices", type="primary"):
            with st.spinner("Calculating mineral indices..."):
                # Import the calculation function
                from agent.mineral_agent import calculate_mineral_indices

                result_str = calculate_mineral_indices.invoke({"site_key": selected_key})
                result = json.loads(result_str)

                # Plot results
                plot_mineral_indices(result)

                # Show interpretation
                st.markdown("---")
                st.subheader("Interpretation Guide")
                st.markdown("""
                **Iron Oxide Index (Red/Blue):**
                - High values (>1.5): Strong oxidation, possible gossans
                - Moderate (1.2-1.5): Some oxidation present
                - Low (<1.2): Limited oxidation

                **Ferrous Index (SWIR1/NIR):**
                - High values (>1.1): Iron-bearing minerals
                - Indicators of magnetite, pyroxene, amphibole

                **Clay Alteration Index (SWIR1/SWIR2):**
                - High values (>1.2): Strong hydrothermal alteration
                - Phyllic or argillic alteration zones
                - Key indicator for porphyry/epithermal systems

                **NDVI (Vegetation):**
                - High values (>0.5): Dense vegetation (may mask minerals)
                - Low values (<0.3): Sparse vegetation (good for mineral mapping)
                """)

    elif analysis_type == "Alteration Zones":
        st.header("🔬 Hydrothermal Alteration Analysis")

        if not data_available:
            st.error("No satellite data available. Please download imagery first.")
            return

        if st.button("Analyze Alteration", type="primary"):
            with st.spinner("Analyzing alteration zones..."):
                from agent.mineral_agent import analyze_alteration_zones

                result_str = analyze_alteration_zones.invoke({"site_key": selected_key})
                result = json.loads(result_str)

                display_alteration_analysis(result)

    elif analysis_type == "AI Chat":
        st.header("💬 AI Exploration Assistant")

        if not api_key:
            st.error("Please provide an Anthropic API key in the sidebar.")
            return

        st.markdown("""
        Ask the AI assistant questions about mineral exploration at this site.

        **Example questions:**
        - What mineral indices should I calculate for this site?
        - Analyze the alteration patterns at this location
        - What are the best exploration targets here?
        - Compare the spectral signatures across different zones
        """)

        # Chat interface
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # User input
        if prompt := st.chat_input(f"Ask about {site_info['name']}..."):
            # Add context to query
            contextualized_prompt = f"""Site: {site_info['name']} ({selected_key})
Target minerals: {', '.join(site_info['minerals'])}
Geology: {site_info['geology']}

User question: {prompt}"""

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        response = run_analysis(contextualized_prompt, api_key)
                        st.markdown(response['response'])
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response['response']
                        })
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><b>GeoScout</b> - Built with Streamlit, LangGraph, and Claude AI</p>
        <p>Sentinel-2 imagery courtesy of ESA Copernicus Program</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
