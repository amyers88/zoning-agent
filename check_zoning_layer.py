"""
Check the base zoning layer information and test queries.
"""

import sys
import os
import json
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

def main():
    from src.config.metro import METRO
    
    # Get layer information
    zoning_url = METRO["BASE_ZONING"]
    info_url = f"{zoning_url}?f=json"
    
    print(f"Fetching layer info from: {zoning_url}")
    
    try:
        # Get layer info
        response = requests.get(info_url, timeout=20)
        response.raise_for_status()
        layer_info = response.json()
        
        # Save full response for inspection
        with open("zoning_layer_info.json", "w") as f:
            json.dump(layer_info, f, indent=2)
        
        # Print basic info
        print(f"\nLayer Name: {layer_info.get('name')}")
        print(f"Description: {layer_info.get('description')}")
        print(f"Type: {layer_info.get('type')}")
        
        # Print fields
        fields = layer_info.get('fields', [])
        print(f"\nAvailable Fields ({len(fields)}):")
        for field in fields:
            print(f"- {field.get('name')} ({field.get('type')}): {field.get('alias', '')}")
        
        # Print extent
        if 'extent' in layer_info:
            print("\nLayer Extent:")
            print(f"  XMin: {layer_info['extent'].get('xmin')}")
            print(f"  YMin: {layer_info['extent'].get('ymin')}")
            print(f"  XMax: {layer_info['extent'].get('xmax')}")
            print(f"  YMax: {layer_info['extent'].get('ymax')}")
        
        # Test query
        print("\nTesting query with a known point (1 Public Square, Nashville, TN):")
        point = {
            "x": -86.77853092361387,
            "y": 36.16717047685326,
            "spatialReference": {"wkid": 4326}
        }
        
        query_url = f"{zoning_url}/query"
        params = {
            "f": "json",
            "geometry": json.dumps(point),
            "geometryType": "esriGeometryPoint",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": False
        }
        
        response = requests.get(query_url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        print(f"\nQuery result: {len(result.get('features', []))} features found")
        for i, feature in enumerate(result.get('features', [])[:5], 1):
            print(f"\nFeature {i}:")
            for key, value in feature.get('attributes', {}).items():
                if value is not None:
                    print(f"  {key}: {value}")
        
        print("\nFull layer info saved to zoning_layer_info.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:500]}")

if __name__ == "__main__":
    main()
