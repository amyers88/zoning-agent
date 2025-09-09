"""
Property analysis module for Metro Nashville GIS data.

This module provides functions to analyze properties by aggregating data from
various Metro Nashville GIS services including parcels, zoning, flood zones,
and development cases.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.config.metro import METRO
from .build_summary import build_summary_stub
from .arcgis_client import (
    geocode_address,
    get_parcel_at_point,
    get_base_zoning,
    get_zoning_overlays,
    get_flood_hazards,
    get_nearby_cases,
    Point,
    Feature
)


def analyze_property(address: str) -> Dict[str, Any]:
    """
    Analyze a property by aggregating data from Metro Nashville GIS services.
    
    Args:
        address: The property address to analyze (e.g., "100 Broadway, Nashville, TN")
        
    Returns:
        A dictionary containing all relevant property information including:
        - Input address and geocoding results
        - Parcel information
        - Zoning details and overlays
        - Flood hazard information
        - Nearby development cases
        - Source references and disclaimers
    """
    # Initialize result with timestamp and input
    result = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "Metro Nashville GIS Services"
        },
        "input": {"address": address}
    }
    
    try:
        # Step 1: Geocode the address
        geo = geocode_address(METRO["GEOCODER"], address)
        if not geo:
            return {"error": "Address not found", **result}
            
        result["input"]["geocode"] = geo
        lon, lat = geo["location"]["x"], geo["location"]["y"]
        
        # Step 2: Get parcel information
        parcel = get_parcel_at_point(METRO["PARCELS"], {"x": lon, "y": lat})
        if not parcel:
            return {
                "error": "No parcel found at the specified location",
                **result
            }
            
        result["parcel"] = {
            "attributes": parcel.get("attributes"),
            "geometry": parcel.get("geometry"),
            "sources": [METRO["PARCELS"]]
        }
        
        # Step 3: Get zoning information
        base_zoning = get_base_zoning(METRO["BASE_ZONING"], parcel)
        overlays = get_zoning_overlays(METRO["ZONING_OVERLAYS"], parcel)
        
        result["zoning"] = {
            "base": base_zoning,
            "overlays": overlays,
            "sources": [METRO["BASE_ZONING"], METRO["ZONING_OVERLAYS"]],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        # Step 4: Get flood hazard information
        flood_approved = get_flood_hazards(METRO["FEMA_APPROVED"], parcel)
        flood_pending = get_flood_hazards(METRO["FEMA_PENDING"], parcel)
        
        result["hazards"] = {
            "flood_approved": flood_approved,
            "flood_pending": flood_pending,
            "sources": [METRO["FEMA_APPROVED"], METRO["FEMA_PENDING"]]
        }
        
        # Step 5: Get nearby development cases
        nearby_cases = get_nearby_cases(METRO["DEV_CASES"], lon, lat, meters=800)
        
        result["context"] = {
            "nearby_development_cases": nearby_cases[:20],  # Limit to 20 most recent
            "total_cases_found": len(nearby_cases),
            "sources": [METRO["DEV_CASES"]]
        }
        
        # Add DTC documentation if in Downtown Code district
        if base_zoning and base_zoning.get("ZONE_CODE") == "DTC":
            result["dtc_docs"] = {
                "pdf": METRO["DTC_PDF"],
                "description": "Downtown Code (DTC) District Information"
            }
        
        # Add disclaimers and metadata
        result["disclaimers"] = [
            "This information is provided as a convenience only and is not an official record.",
            "Metro GIS data should be verified with the relevant Metro departments.",
            "Flood zone information is from FEMA layers; see FEMA for official determinations.",
            "Zoning information is subject to change. Verify with Metro Planning Department."
        ]
        
        # Generate summary
        result["summary"] = build_summary_stub(result)
        
        # Create the final structured result
        structured_result = {
            "input": {"address": address, "geocode": result["input"].get("geocode")},
            "parcel": {
                "attributes": result.get("parcel", {}).get("attributes"),
                "geometry": result.get("parcel", {}).get("geometry"),
                "sources": [METRO["PARCELS"]],
            },
            "zoning": {
                "base": result.get("zoning", {}).get("base"),
                "overlays": result.get("zoning", {}).get("overlays", []),
                "sources": [METRO["BASE_ZONING"], METRO["ZONING_OVERLAYS"]],
            },
            "constraints": {
                "flood_approved": result.get("hazards", {}).get("flood_approved", []),
                "flood_pending": result.get("hazards", {}).get("flood_pending", []),
                "sources": [METRO["FEMA_APPROVED"], METRO["FEMA_PENDING"]],
            },
            "context": {
                "nearby_development_cases": result.get("context", {}).get("nearby_development_cases", []),
                "sources": [METRO["DEV_CASES"]],
            },
            "dtc_docs": {"pdf": METRO["DTC_PDF"]} if result.get("dtc_docs") else {},
            "disclaimers": [
                "Metro GIS data; verify with Planning/Codes.",
                "Flood info from FEMA layers; see FEMA MSC for official determinations.",
            ],
            "metadata": result.get("metadata", {})
        }
        
        # Add build summary to the structured result
        structured_result["build_summary"] = result["summary"]
        
        result["metadata"]["status"] = "success"
        return structured_result
        
    except Exception as e:
        result["error"] = f"Error analyzing property: {str(e)}"
        result["metadata"]["status"] = "error"
        return result


if __name__ == "__main__":
    # Example usage
    import json
    
    # Test with a sample address
    address = "100 Broadway, Nashville, TN"
    print(f"Analyzing property: {address}")
    
    result = analyze_property(address)
    
    # Print summary
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nAnalysis Complete!")
        print(f"Address: {result['input']['address']}")
        
        if "parcel" in result and "attributes" in result["parcel"]:
            attrs = result["parcel"]["attributes"]
            print(f"Parcel ID: {attrs.get('PIN', 'N/A')}")
            print(f"Property Address: {attrs.get('PROPADDR', 'N/A')}")
        
        if "zoning" in result and "base" in result["zoning"] and result["zoning"]["base"]:
            zone = result["zoning"]["base"]
            print(f"Zoning: {zone.get('ZONE_CODE', 'N/A')} - {zone.get('ZONE_DESC', 'N/A')}")
        
        if "hazards" in result:
            hazards = result["hazards"]
            print(f"Flood Zones (Approved): {[h.get('FloodZone') for h in hazards.get('flood_approved', [])] or 'None'}")
            print(f"Flood Zones (Pending): {[h.get('FloodZone') for h in hazards.get('flood_pending', [])] or 'None'}")
        
        if "context" in result and "nearby_development_cases" in result["context"]:
            cases = result["context"]["nearby_development_cases"]
            print(f"\nNearby Development Cases: {len(cases)} (showing up to 20)")
            for i, case in enumerate(cases[:5], 1):  # Show first 5 cases
                print(f"  {i}. {case.get('CASE_NUMBER')} - {case.get('CASE_TYPE')}")
                print(f"     {case.get('PROJECT_NAME')}")
                print(f"     Status: {case.get('STATUS')}")
    
    # Save full results to file
    with open("property_analysis.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nFull analysis saved to property_analysis.json")
