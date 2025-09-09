"""
Test script for Metro Nashville parcel lookup.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

def main():
    from src.integrations.metro.arcgis_client import get_parcel_at_point
    from src.config.metro import METRO
    
    # Test points (from successful geocoding)
    test_points = [
        {"name": "100 Broadway", "x": -86.77493036930412, "y": 36.16233809587476},
        {"name": "1 Public Square", "x": -86.77853092361387, "y": 36.16717047685326}
    ]
    
    print("Testing Metro Nashville Parcel Lookup\n" + "="*40)
    
    for point in test_points:
        print(f"\n🔍 Looking up parcel at {point['name']} ({point['y']}, {point['x']})")
        try:
            parcel = get_parcel_at_point(METRO["PARCELS"], point)
            if parcel and 'attributes' in parcel:
                attrs = parcel['attributes']
                print("✅ Found parcel with attributes:")
                
                # Print all available attributes
                for key, value in attrs.items():
                    print(f"   {key}: {value}")
                
                # Print geometry info if available
                if 'geometry' in parcel:
                    geom_type = type(parcel['geometry']).__name__
                    print(f"\n   Geometry: {geom_type}")
                    if geom_type == 'dict' and 'x' in parcel['geometry'] and 'y' in parcel['geometry']:
                        print(f"   Location: {parcel['geometry']['y']}, {parcel['geometry']['x']}")
                
                # Print the full response to a file for inspection
                with open('parcel_response.json', 'w') as f:
                    json.dump(parcel, f, indent=2)
                print("\n   Full response saved to parcel_response.json")
            else:
                print("❌ No parcel found at this location")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
