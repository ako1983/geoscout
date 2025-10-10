#!/usr/bin/env python3
"""
Download Sentinel-2 imagery for mineral exploration sites.
Uses Google Earth Engine API to fetch cloud-free scenes from 2024.
"""

import ee
from datetime import datetime
import urllib.request
import time
import ssl
import certifi
import zipfile
import os
import glob

# Site coordinates
SITES = {
    'mountain_pass_ca': {
        'name': 'Mountain Pass, CA',
        'lon': -115.5408,
        'lat': 35.4881,
        'buffer': 5000  # meters
    },
    'bingham_canyon_ut': {
        'name': 'Bingham Canyon, UT',
        'lon': -112.1500,
        'lat': 40.5231,
        'buffer': 5000
    },
    'bokan_mountain_ak': {
        'name': 'Bokan Mountain, AK',
        'lon': -132.1583,
        'lat': 54.8867,
        'buffer': 5000
    }
}

# Bands to download: RGB (4,3,2) + NIR/SWIR (8,11,12)
BANDS = ['B4', 'B3', 'B2', 'B8', 'B11', 'B12']
DATE_START = '2024-01-01'
DATE_END = '2024-12-31'


def initialize_ee(service_account_file):
    """Initialize Earth Engine with service account credentials."""
    print("Initializing Google Earth Engine...")

    # Read service account credentials
    credentials = ee.ServiceAccountCredentials(
        email=None,  # Will be read from JSON
        key_file=service_account_file
    )

    ee.Initialize(credentials)
    print("✓ Earth Engine initialized successfully")


def get_best_scene(point, site_key):
    """Get the best (least cloudy) Sentinel-2 scene for a location."""
    site_info = SITES[site_key]
    print(f"\nSearching for imagery for {site_info['name']}...")

    # Create region of interest
    roi = point.buffer(site_info['buffer'])

    # Query Sentinel-2 collection
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(roi)
                  .filterDate(DATE_START, DATE_END)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .select(BANDS))

    # Get collection size
    count = collection.size().getInfo()
    print(f"  Found {count} scenes with <20% cloud cover")

    if count == 0:
        print(f"  ⚠ No suitable scenes found for {site_info['name']}")
        return None

    # Get the least cloudy scene
    best_scene = collection.sort('CLOUDY_PIXEL_PERCENTAGE').first()

    # Get metadata
    props = best_scene.getInfo()['properties']
    date = props['system:time_start']
    cloud_cover = props['CLOUDY_PIXEL_PERCENTAGE']

    # Convert timestamp to readable date
    date_str = datetime.fromtimestamp(date / 1000).strftime('%Y-%m-%d')

    print(f"  ✓ Best scene: {date_str} (Cloud cover: {cloud_cover:.1f}%)")

    return best_scene, roi


def download_scene(image, roi, site_key, site_info):
    """Download a Sentinel-2 scene as GeoTIFF."""
    output_file = f"geoscout/data/{site_key}_sentinel2.tif"
    zip_file = f"geoscout/data/{site_key}_sentinel2.zip"

    print(f"\nDownloading {site_info['name']}...")
    print(f"  Output: {output_file}")

    try:
        # Get download URL from Earth Engine
        url = image.getDownloadURL({
            'scale': 10,  # 10m resolution
            'crs': 'EPSG:4326',
            'fileFormat': 'GeoTIFF',
            'region': roi,
            'filePerBand': False
        })

        # Download the ZIP file with SSL context
        print(f"  Requesting download from Earth Engine...")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=ssl_context) as response:
            with open(zip_file, 'wb') as out_file:
                out_file.write(response.read())

        # Extract the GeoTIFF from ZIP
        print(f"  Extracting GeoTIFF from ZIP...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Find the .tif file in the zip
            tif_files = [f for f in zip_ref.namelist() if f.endswith('.tif')]
            if tif_files:
                # Extract the first .tif file
                zip_ref.extract(tif_files[0], 'geoscout/data/')
                # Rename to our desired filename
                extracted_path = f"geoscout/data/{tif_files[0]}"
                if os.path.exists(output_file):
                    os.remove(output_file)
                os.rename(extracted_path, output_file)
                print(f"  ✓ Extracted: {output_file}")
            else:
                raise Exception("No .tif file found in ZIP archive")

        # Clean up ZIP file
        os.remove(zip_file)

        print(f"  ✓ Downloaded successfully: {output_file}")
        return True

    except Exception as e:
        print(f"  ✗ Error downloading: {e}")
        # Clean up partial files
        if os.path.exists(zip_file):
            os.remove(zip_file)
        return False


def main():
    """Main function to download all scenes."""
    print("=" * 60)
    print("Sentinel-2 Imagery Download for Mineral Exploration Sites")
    print("=" * 60)

    # Initialize Earth Engine
    service_account_file = 'gen-lang-client-0926459788-13e512ba6dbd.json'
    initialize_ee(service_account_file)

    # Process each site
    successful = 0
    failed = 0

    for site_key, site_info in SITES.items():
        try:
            # Create point geometry
            point = ee.Geometry.Point([site_info['lon'], site_info['lat']])

            # Get best scene
            result = get_best_scene(point, site_key)

            if result is None:
                failed += 1
                continue

            best_scene, roi = result

            # Download scene
            if download_scene(best_scene, roi, site_key, site_info):
                successful += 1
            else:
                failed += 1

        except Exception as e:
            print(f"\n✗ Error processing {site_info['name']}: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Successfully downloaded: {successful} scenes")
    if failed > 0:
        print(f"✗ Failed: {failed} scenes")
    print("\nBands downloaded: B4 (Red), B3 (Green), B2 (Blue), B8 (NIR), B11 (SWIR1), B12 (SWIR2)")


if __name__ == '__main__':
    main()
