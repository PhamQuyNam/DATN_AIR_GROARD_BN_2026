import urllib.request
import json

try:
    # 1. Get the download URL for Vietnam ADM1 (Provinces) from Geoboundaries
    print("Fetching Geoboundaries metadata...")
    req_meta = urllib.request.Request("https://www.geoboundaries.org/api/current/gbOpen/VNM/ADM1/")
    res_meta = urllib.request.urlopen(req_meta)
    meta = json.loads(res_meta.read())
    
    download_url = meta['gjDownloadURL']
    print(f"Downloading GeoJSON from {download_url}...")
    
    # 2. Download the GeoJSON containing all provinces
    req_gj = urllib.request.Request(download_url)
    res_gj = urllib.request.urlopen(req_gj)
    geojson_data = json.loads(res_gj.read())
    
    # 3. Filter for Bac Ninh
    bacninh_feature = None
    for feature in geojson_data['features']:
        name = feature['properties'].get('shapeName', '').lower()
        if 'bac ninh' in name or 'bắc ninh' in name:
            bacninh_feature = feature
            break
            
    if bacninh_feature:
        # Create a new FeatureCollection for just Bac Ninh
        final_geojson = {
            "type": "FeatureCollection",
            "features": [bacninh_feature]
        }
        with open('data/bacninh.json', 'w', encoding='utf-8') as f:
            json.dump(final_geojson, f, ensure_ascii=False)
        print("Successfully saved accurate Bac Ninh GeoJSON boundary!")
    else:
        print("Bac Ninh not found in the dataset.")
        
except Exception as e:
    print("An error occurred:", e)
