"""
Test script for the Metro Nashville property analyzer.
"""

import sys
import os
import json
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

def main():
    from src.integrations.metro.analyzer import analyze_property
    
    # Default test address
    test_addresses = ["1 Public Square, Nashville, TN"]
    
    # Use command line arguments if provided
    if len(sys.argv) > 1:
        test_addresses = [" ".join(sys.argv[1:])]
    else:
        # Or use a list of test addresses
        test_addresses = [
            "1 Public Square, Nashville, TN",
            "222 2nd Ave S, Nashville, TN",
            "100 Broadway, Nashville, TN"
        ]
    
    for test_address in test_addresses:
        print(f"\n{'='*80}")
        print(f"Analyzing property: {test_address}")
        print("=" * (len(test_address) + 19))  # Match the length of the address line
        print("\n=== Detailed Property Analysis ===\n")
        
        try:
            # Run the analysis
            result = analyze_property(test_address)
            
            # 1. Input Information
            print("\n📌 Input Information")
            print(f"   Address: {result.get('input', {}).get('address', 'N/A')}")
            if 'geocode' in result.get('input', {}):
                loc = result['input']['geocode'].get('location', {})
                print(f"   Location: {loc.get('y', 'N/A')}, {loc.get('x', 'N/A')}")
            
            # 2. Parcel Information
            print("\n🏠 Parcel Information")
            # Parcel info
            if "parcel" in result and "attributes" in result["parcel"]:
                attrs = result["parcel"]["attributes"]
                print(f"\nParcel ID: {attrs.get('APN', 'N/A')}")
                print(f"Owner: {attrs.get('Owner', 'N/A')}")
                print(f"Address: {attrs.get('PropHouse', '')} {attrs.get('PropStreet', '')}")
                print(f"City/State/Zip: {attrs.get('PropCity', '')}, {attrs.get('PropState', '')} {attrs.get('PropZip', '')}")
                print(f"Land Use: {attrs.get('LUDesc', 'N/A')} ({attrs.get('LUCode', 'N/A')})")
                print(f"Acres: {attrs.get('Acres', 'N/A')} (Deeded: {attrs.get('DeededAcreage', 'N/A')})")
            else:
                print("   No parcel information found")
            
            # 3. Zoning Information
            print("\n🏛️  Zoning Information")
            zoning = result.get('zoning', {})
            if 'base' in zoning and zoning['base']:
                print(f"   Base Zone: {zoning['base'].get('ZONE_CODE', 'N/A')} - {zoning['base'].get('ZONE_DESC', 'N/A')}")
            else:
                print("   No base zoning information found")
                
            # 4. Zoning Overlays
            if 'overlays' in zoning and zoning['overlays']:
                print("   Overlays:")
                for overlay in zoning['overlays'][:5]:  # Limit to first 5 overlays
                    print(f"   - {overlay.get('ZONE_CODE', 'N/A')}: {overlay.get('ZONE_DESC', 'N/A')}")
                    if len(zoning['overlays']) > 5:
                        print(f"   ... and {len(zoning['overlays']) - 5} more overlays")
            
            # 5. Constraints
            print("\n⚠️  Constraints")
            constraints = result.get('constraints', {})
            
            # Flood zones
            if 'flood_approved' in constraints and constraints['flood_approved']:
                zones = [f.get('FLOODZONE', 'Unknown') for f in constraints['flood_approved']]
                print(f"   Flood Zones (Approved): {', '.join(zones) if zones else 'None'}")
            else:
                print("   Flood Zones (Approved): None")
                
            if 'flood_pending' in constraints and constraints['flood_pending']:
                zones = [f.get('FLOODZONE', 'Unknown') for f in constraints['flood_pending']]
                print(f"   Flood Zones (Pending): {', '.join(zones) if zones else 'None'}")
            else:
                print("   Flood Zones (Pending): None")
            
            # 6. Nearby Development
            print("\n🏗️  Nearby Development Activity")
            cases = result.get('development_cases', [])
            if cases:
                print(f"   Found {len(cases)} nearby development cases:")
                for case in cases[:5]:
                    print(f"\n   🏢 {case.get('CASE_NUMBER', 'N/A')} - {case.get('CASE_TYPE', 'N/A')}")
                    print(f"      Project: {case.get('PROJECT_NAME', 'N/A')}")
                    print(f"      Status: {case.get('STATUS', 'N/A')}")
                    print(f"      Address: {case.get('ADDRESS', 'N/A')}")
                    if 'APPLICATION_DATE' in case:
                        print(f"      Applied: {case['APPLICATION_DATE']}")
            else:
                print("   No nearby development cases found")
            
            # Display summary if available
            if "summary" in result:
                print("\n📋 Summary")
                summary = result["summary"]
                print(f"   District: {summary.get('district', 'N/A')}")
                
                if summary.get('lot_area_sqft'):
                    print(f"   Lot Area: {summary['lot_area_sqft']:,.0f} sq ft ({summary.get('lot_area_acres', 0):.2f} acres)")
                
                if 'by_right' in summary:
                    print("\n   By Right:")
                    for key, value in summary['by_right'].items():
                        if value:  # Only show non-None values
                            print(f"     {key.replace('_', ' ').title()}: {value}")
                
                if summary.get('flags'):
                    print("\n   🚩 Flags:")
                    for flag in summary['flags']:
                        print(f"     • {flag}")
                
                if summary.get('overlays'):
                    print("\n   🏙️  Overlays:")
                    for overlay in summary['overlays']:
                        print(f"     • {overlay}")
            
            # Save full results to file with timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"property_analysis_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
                
            print(f"\n✅ Full analysis saved to {filename}")
            
        except Exception as e:
            print(f"\n❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Add some space between multiple addresses
        print("\n" + "-" * 80 + "\n")

if __name__ == "__main__":
    main()
