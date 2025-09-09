"""
Test script for Metro Nashville geocoding service.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

def main():
    from src.integrations.metro.arcgis_client import metro_geocode
    
    test_addresses = [
        "100 Broadway, Nashville, TN",
        "222 2nd Ave S, Nashville, TN",
        "1 Nashville Place, Nashville, TN",
        "1 Public Square, Nashville, TN"
    ]
    
    print("Testing Metro Nashville Geocoding Service\n" + "="*40)
    
    for address in test_addresses:
        print(f"\n🔍 Geocoding: {address}")
        try:
            result = metro_geocode(address)
            if result:
                print(f"✅ Found: {result.get('address', 'N/A')}")
                print(f"   Score: {result.get('score', 'N/A')}")
                print(f"   Location: {result.get('location', {}).get('y', 'N/A')}, {result.get('location', {}).get('x', 'N/A')}")
            else:
                print("❌ No results found")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
