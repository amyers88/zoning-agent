"""
Check available fields in the Metro Nashville parcels layer.
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
    parcels_url = METRO["PARCELS"]
    info_url = f"{parcels_url}?f=json"
    
    print(f"Fetching layer info from: {parcels_url}")
    
    try:
        response = requests.get(info_url, timeout=20)
        response.raise_for_status()
        layer_info = response.json()
        
        # Save full response for inspection
        with open("parcel_layer_info.json", "w") as f:
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
        
        print("\nFull layer info saved to parcel_layer_info.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:500]}")

if __name__ == "__main__":
    main()
