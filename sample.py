# use this to write the script! 
import os
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import folium
import json

# Optionally: spectral library tools
# from spectral import open_image  # if you use “spectral” package

def read_hyperspectral_cube(tiff_path):
    """
    Reads a multi-band GeoTIFF (hyperspectral cube) and returns
    a NumPy array with shape (bands, rows, cols) and metadata.
    """
    with rasterio.open(tiff_path) as src:
        meta = src.meta.copy()
        # Read all bands
        data = src.read()  # shape: (band_count, height, width)
    return data, meta

def visualize_rgb_composite(data, bands=(30, 20, 10), meta=None, vmin=0, vmax=None, title="RGB composite"):
    """
    Visualizes an RGB composite from the cube.
    bands: tuple of 3 band indices (band numbers starting 0) — (R, G, B)
    """
    r = data[bands[0], :, :]
    g = data[bands[1], :, :]
    b = data[bands[2], :, :]
    rgb = np.stack([r, g, b], axis=-1)
    # Normalize for display
    if vmax is None:
        vmax = np.percentile(rgb, 98)
    norm = Normalize(vmin=vmin, vmax=vmax)
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    ax.imshow(norm(rgb))
    ax.set_title(title)
    ax.axis("off")
    plt.show()

def compute_simple_ratio_index(data, band_num1, band_num2):
    """
    Compute a simple ratio: band1 / band2 (avoid division by zero).
    Returns a 2D array.
    """
    b1 = data[band_num1, :, :].astype(np.float32)
    b2 = data[band_num2, :, :].astype(np.float32)
    # avoid zero
    with np.errstate(divide='ignore', invalid='ignore'):
        idx = b1 / b2
    # mask invalid
    idx = np.nan_to_num(idx, nan=0.0, posinf=0.0, neginf=0.0)
    return idx

def plot_index_map(idx_array, title="Index map"):
    """
    Plot a 2D index array with colorbar.
    """
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    im = ax.imshow(idx_array, cmap='viridis')
    fig.colorbar(im, ax=ax, shrink=0.7)
    ax.set_title(title)
    ax.axis("off")
    plt.show()

def save_index_as_geotiff(idx, meta, out_path):
    """
    Save the 2D index (single band) as a GeoTIFF using metadata.
    """
    # adjust metadata
    meta2 = meta.copy()
    meta2.update({
        "count": 1,
        "dtype": "float32"
    })
    with rasterio.open(out_path, "w", **meta2) as dst:
        dst.write(idx.astype('float32'), 1)

def make_map_overlay(idx, meta, colormap='viridis', alpha=0.6):
    """
    Create a folium map and overlay the index as an image overlay.
    Warning: this is a rough method—requires warping, bounds extraction.
    """
    # Determine bounds (in lat/lon) from metadata
    # src transform gives mapping pixel->map coords (in spatial reference)
    transform = meta['transform']
    height = idx.shape[0]
    width = idx.shape[1]
    # pixel (0,0) upper left
    ulx, uly = transform * (0, 0)
    # pixel (width, height)
    lrx, lry = transform * (width, height)
    # bounds as [[south, west], [north, east]]
    bounds = [[lry, ulx], [uly, lrx]]
    # Normalize to 0–255 image
    normed = (idx - np.min(idx)) / (np.max(idx) - np.min(idx) + 1e-9)
    img = (plt.cm.get_cmap(colormap)(normed) * 255).astype(np.uint8)
    # Convert to PNG or image bytes
    # Here we write a temporary PNG
    import tempfile
    from PIL import Image
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    Image.fromarray(img[:, :, :3]).save(tmp.name)
    m = folium.Map(location=[(bounds[0][0] + bounds[1][0]) / 2,
                             (bounds[0][1] + bounds[1][1]) / 2],
                   zoom_start=10)
    folium.raster_layers.ImageOverlay(
        name=title,
        image=tmp.name,
        bounds=bounds,
        opacity=alpha,
        interactive=True,
        cross_origin=False,
        zindex=1,
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m

##############################
# --- Example usage flow ---
##############################

if __name__ == "__main__":
    # Example: paths you change
    hyperion_tiff = "/path/to/hyperion_cube.tif"
    wyvern_tiff = "/path/to/wyvern_cube.tif"

    # Read Hyperion
    data_h, meta_h = read_hyperspectral_cube(hyperion_tiff)
    print("Hyperion cube shape:", data_h.shape)
    # Visualize a rough RGB composite (pick bands, experiment)
    visualize_rgb_composite(data_h, bands=(60, 40, 20), title="Hyperion RGB-ish")

    # Compute a simple ratio (band 80 / band 120) — arbitrary pick
    idx = compute_simple_ratio_index(data_h, band_num1=80, band_num2=120)
    plot_index_map(idx, title="Hyperspectral ratio (80 / 120)")

    # Save the index
    save_index_as_geotiff(idx, meta_h, "hyperion_ratio_80_120.tif")

    # Optionally: overlay on map (if geo metadata works out)
    # m = make_map_overlay(idx, meta_h)
    # m.save("hyperion_index_map.html")

    # Repeat for Wyvern
    data_w, meta_w = read_hyperspectral_cube(wyvern_tiff)
    print("Wyvern cube shape:", data_w.shape)
    visualize_rgb_composite(data_w, bands=(5, 3, 1), title="Wyvern RGB-ish")
    idx_w = compute_simple_ratio_index(data_w, band_num1=10, band_num2=15)
    plot_index_map(idx_w, title="Wyvern ratio (10 / 15)")
    save_index_as_geotiff(idx_w, meta_w, "wyvern_ratio_10_15.tif")