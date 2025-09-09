"""
ArcGIS REST API client for Metro Nashville GIS services.

This module provides functions to interact with Metro Nashville's ArcGIS REST services,
including geocoding addresses, parcel lookups, and spatial queries.
"""

import json
from urllib.parse import quote
from typing import Dict, Optional, Any, List, TypedDict, Union
import requests
from src.config.metro import METRO


class Point(TypedDict):
    """Represents a geographic point with x (longitude) and y (latitude) coordinates."""
    x: float
    y: float


class Geometry(TypedDict, total=False):
    """Represents a geographic geometry with coordinates and spatial reference."""
    x: float
    y: float
    rings: List[List[List[float]]]
    spatialReference: Dict[str, Any]


class Feature(TypedDict, total=False):
    """Represents a feature from an ArcGIS Feature Service response."""
    attributes: Dict[str, Any]
    geometry: Geometry


def geocode_address(geocoder_url: str, single_line: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    """
    Geocode an address using Metro Nashville's geocoding service.

    Args:
        geocoder_url: The URL of the geocoding service
        single_line: The address to geocode (e.g., "100 Broadway, Nashville, TN")
        timeout: Request timeout in seconds

    Returns:
        Dict containing match address, score, and location (lon/lat in WGS84) if found,
        None if no match found

    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the response is not valid JSON or is missing required fields
    """
    params = {
        "f": "json",
        "SingleLine": single_line,
        "outFields": "Match_addr,Addr_type,Score",
        "maxLocations": 1,
        "outSR": 4326,  # WGS84
    }
    
    try:
        r = requests.get(
            f"{geocoder_url}/findAddressCandidates",
            params=params,
            timeout=timeout
        )
        r.raise_for_status()
        
        js = r.json()
        if not js.get("candidates"):
            return None
            
        candidate = js["candidates"][0]
        return {
            "match_addr": candidate.get("address"),
            "score": candidate.get("score"),
            "location": {
                "x": candidate["location"]["x"],  # longitude
                "y": candidate["location"]["y"]   # latitude
            }
        }
        
    except requests.exceptions.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")
    except KeyError as e:
        raise ValueError(f"Missing expected field in response: {e}")


# Convenience function using default Metro Nashville geocoder
def get_parcel_at_point(parcels_url: str, point: Point, out_fields: str = None) -> Optional[Feature]:
    """
    Find a parcel that intersects the given point.

    Args:
        parcels_url: The URL of the parcels feature service
        point: Dictionary with 'x' (longitude) and 'y' (latitude) keys
        out_fields: Comma-separated list of fields to return. Defaults to common parcel fields.

    Returns:
        Feature dictionary with attributes and geometry if found, None otherwise

    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the response is not valid JSON or is missing required fields
    """
    # Default fields to request if none specified
    if out_fields is None:
        out_fields = "OBJECTID,ParID,APN,Owner,PropAddr,PropHouse,PropStreet,PropCity,PropState,PropZip,Acres,DeededAcreage,STANPAR,LUCode,LUDesc"
    
    params = {
        "f": "json",
        "geometry": json.dumps({"x": point["x"], "y": point["y"], "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": True,
        "outSR": 4326,
        "returnExtentOnly": False,
        "returnDistinctValues": False,
        "returnZ": False,
        "returnM": False
    }
    
    try:
        r = requests.get(f"{parcels_url}/query", params=params, timeout=20)
        r.raise_for_status()
        
        js = r.json()
        features = js.get("features", [])
        return features[0] if features else None
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise ValueError(f"Failed to parse parcel data: {e}")


def metro_geocode(address: str) -> Optional[Dict[str, Any]]:
    """
    Geocode an address using Metro Nashville's default geocoding service.
    
    Args:
        address: The address to geocode (e.g., "100 Broadway, Nashville, TN")
        
    Returns:
        Geocoding result or None if no match found
    """
    return geocode_address(METRO["GEOCODER"], address)


def _encode_geometry_for_query(geom_json: Dict[str, Any]) -> str:
    """URL-encode a geometry JSON for use in ArcGIS REST API queries.
    
    Args:
        geom_json: Geometry dictionary in ArcGIS JSON format
        
    Returns:
        URL-encoded geometry string
    """
    return quote(json.dumps(geom_json))


def intersect_layer_with_polygon(
    layer_url: str, 
    polygon_geom: Dict[str, Any], 
    out_fields: str = "*",
    in_sr: int = 102100,
    out_sr: int = 4326
) -> List[Dict[str, Any]]:
    """
    Find features in a layer that intersect with the given polygon.
    
    Args:
        layer_url: URL of the ArcGIS Feature Service layer
        polygon_geom: Polygon geometry in ArcGIS JSON format
        out_fields: Comma-separated list of fields to return (default: all fields)
        in_sr: Spatial reference of input geometry (default: Web Mercator)
        out_sr: Spatial reference for output features (default: WGS84)
        
    Returns:
        List of matching features with attributes
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the response is not valid JSON
    """
    params = {
        "f": "json",
        "geometry": json.dumps(polygon_geom),
        "geometryType": "esriGeometryPolygon",
        "inSR": in_sr,
        "outSR": out_sr,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": False,
    }
    
    try:
        r = requests.post(f"{layer_url}/query", data=params, timeout=30)
        r.raise_for_status()
        return r.json().get("features", [])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")


def get_base_zoning(base_zoning_url: str, parcel: Feature) -> Optional[Dict[str, Any]]:
    """
    Get the base zoning for a parcel.
    
    Args:
        base_zoning_url: URL of the base zoning layer (expects StatePlane Tennessee FIPS 4100 Feet)
        parcel: Parcel feature from get_parcel_at_point() in WGS84 (lat/lon)
        
    Returns:
        Zoning attributes if found, None otherwise
    """
    if not parcel or 'geometry' not in parcel:
        return None
    
    # First, get the point coordinates from the parcel geometry
    geometry = parcel['geometry']
    
    # Handle different geometry formats
    if 'x' in geometry and 'y' in geometry:
        # Point geometry
        point = {
            'x': geometry['x'],
            'y': geometry['y'],
            'spatialReference': geometry.get('spatialReference', {'wkid': 4326})
        }
    elif 'rings' in geometry and geometry['rings'] and geometry['rings'][0]:
        # Polygon geometry - use the first point of the first ring
        point = {
            'x': geometry['rings'][0][0][0],
            'y': geometry['rings'][0][0][1],
            'spatialReference': geometry.get('spatialReference', {'wkid': 4326})
        }
    else:
        print(f"Unsupported geometry format: {json.dumps(geometry, indent=2)[:200]}...")
        return None
    
    # Convert to StatePlane Tennessee FIPS 4100 Feet (WKID 2274)
    transform_url = "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Utilities/Geometry/GeometryServer/project"
    params = {
        'f': 'json',
        'inSR': 4326,  # WGS84
        'outSR': 2274,  # StatePlane Tennessee FIPS 4100 Feet
        'geometries': json.dumps({
            'geometryType': 'esriGeometryPoint',
            'geometries': [point]
        })
    }
    
    try:
        response = requests.post(transform_url, data=params, timeout=20)
        response.raise_for_status()
        transformed_geoms = response.json().get('geometries', [])
        
        if not transformed_geoms:
            return None
            
        transformed_point = transformed_geoms[0]
        
        # Query the zoning layer with the transformed point
        query_url = f"{base_zoning_url}/query"
        params = {
            'f': 'json',
            'geometry': json.dumps(transformed_point),
            'geometryType': 'esriGeometryPoint',
            'inSR': 2274,  # StatePlane Tennessee FIPS 4100 Feet
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'ZONE_DESC,CASE_NO,ORDINANCE,NAME',
            'returnGeometry': False
        }
        
        response = requests.get(query_url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        features = result.get('features', [])
        if not features:
            return None
            
        # Get the first feature's attributes
        attrs = features[0].get('attributes', {})
        
        return {
            'ZONE_CODE': attrs.get('ZONE_DESC'),
            'ZONE_DESC': attrs.get('ZONE_DESC'),
            'CASE_NO': attrs.get('CASE_NO'),
            'ORDINANCE': attrs.get('ORDINANCE'),
            'NAME': attrs.get('NAME')
        }
        
    except Exception as e:
        print(f"Error getting base zoning: {str(e)}")
        return None


def get_zoning_overlays(overlay_url: str, parcel_feature: Feature) -> List[Dict[str, Any]]:
    """
    Get all zoning overlays that intersect with a parcel.
    
    Args:
        overlay_url: URL of the zoning overlays layer
        parcel_feature: Parcel feature from get_parcel_at_point()
        
    Returns:
        List of overlay attributes
    """
    if not parcel_feature or "geometry" not in parcel_feature:
        return []
        
    features = intersect_layer_with_polygon(
        overlay_url,
        parcel_feature["geometry"],
        out_fields="*"
    )
    return [f["attributes"] for f in features]


def get_flood_hazards(fema_layer_url: str, parcel_feature: Feature) -> List[Dict[str, Any]]:
    """
    Get FEMA flood hazard information for a parcel.
    
    Args:
        fema_layer_url: URL of the FEMA flood hazard layer
        parcel_feature: Parcel feature from get_parcel_at_point()
        
    Returns:
        List of flood hazard attributes including FloodZone, ZoneDescription, etc.
        
    Example:
        [{
            'FloodZone': 'AE',
            'ZoneDescription': 'Area with 1% annual chance of flooding',
            'AdoptedDate': 1234567890000,
            'OBJECTID': 12345
        }]
    """
    if not parcel_feature or "geometry" not in parcel_feature:
        return []
        
    features = intersect_layer_with_polygon(
        fema_layer_url,
        parcel_feature["geometry"],
        out_fields="FloodZone,ZoneDescription,AdoptedDate,OBJECTID"
    )
    return [f["attributes"] for f in features]


def get_nearby_cases(
    dev_cases_url: str, 
    lon: float, 
    lat: float, 
    meters: int = 800,
    out_fields: str = "*"
) -> List[Dict[str, Any]]:
    """
    Get development cases near a geographic point.
    
    Args:
        dev_cases_url: URL of the development cases layer
        lon: Longitude of the center point
        lat: Latitude of the center point
        meters: Search radius in meters (default: 800m)
        out_fields: Comma-separated list of fields to return (default: all fields)
        
    Returns:
        List of development case attributes
        
    Example:
        [{
            'CASE_NUMBER': '2023-001',
            'CASE_TYPE': 'SP',
            'STATUS': 'Under Review',
            'PROJECT_NAME': 'New Development',
            'ADDRESS': '123 Main St',
            'APPLICATION_DATE': 1672531200000,
            'STATUS_DATE': 1675209600000
        }]
    """
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "distance": meters,
        "units": "esriSRUnit_Meter",
        "outFields": out_fields,
        "returnGeometry": False,
        "orderByFields": "STATUS_DATE DESC"  # Most recent first
    }
    
    try:
        r = requests.get(f"{dev_cases_url}/query", params=params, timeout=20)
        r.raise_for_status()
        return [f["attributes"] for f in r.json().get("features", [])]
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to fetch development cases: {e}")


if __name__ == "__main__":
    # Example usage
    print("Testing geocoding:")
    result = metro_geocode("100 Broadway, Nashville, TN")
    if not result:
        print("No geocoding match found")
        exit(1)
        
    print(f"Geocoding result: {result}")
    
    # Find the parcel at that location
    print("\nTesting parcel lookup:")
    point = {"x": result["location"]["x"], "y": result["location"]["y"]}
    parcel = get_parcel_at_point(
        parcels_url=METRO["PARCELS"],
        point=point,
        out_fields="PIN,APN,OWNER,PROPADDR"
    )
    
    if not parcel:
        print("No parcel found at this location")
        exit(1)
        
    print(f"Found parcel: {parcel.get('attributes', {}).get('PROPADDR')}")
    print(f"Parcel ID: {parcel.get('attributes', {}).get('PIN')}")
    
    # Get base zoning
    print("\nTesting base zoning lookup:")
    zoning = get_base_zoning(METRO["BASE_ZONING"], parcel)
    if zoning:
        print(f"Base zoning: {zoning.get('ZONE_CODE')} - {zoning.get('ZONE_DESC')}")
    else:
        print("No zoning information found")
    
    # Get zoning overlays
    print("\nTesting zoning overlays:")
    overlays = get_zoning_overlays(METRO["ZONING_OVERLAYS"], parcel)
    if overlays:
        print(f"Found {len(overlays)} overlay(s):")
        for i, ov in enumerate(overlays, 1):
            print(f"  {i}. {ov.get('OVERLAY')} - {ov.get('OVERLAY_DESC')}")
    else:
        print("No zoning overlays found")
    
    # Get FEMA flood hazards (approved)
    print("\nTesting FEMA flood hazards (approved):")
    flood_hazards = get_flood_hazards(METRO["FEMA_APPROVED"], parcel)
    if flood_hazards:
        print(f"Found {len(flood_hazards)} flood hazard zone(s):")
        for i, fz in enumerate(flood_hazards, 1):
            print(f"  {i}. {fz.get('FloodZone')} - {fz.get('ZoneDescription')}")
    else:
        print("No FEMA flood hazards found (approved)")
    
    # Get FEMA flood hazards (pending)
    print("\nTesting FEMA flood hazards (pending):")
    pending_hazards = get_flood_hazards(METRO["FEMA_PENDING"], parcel)
    if pending_hazards:
        print(f"Found {len(pending_hazards)} pending flood hazard zone(s):")
        for i, fz in enumerate(pending_hazards, 1):
            print(f"  {i}. {fz.get('FloodZone')} - {fz.get('ZoneDescription')}")
    else:
        print("No pending FEMA flood hazards found")
    
    # Get nearby development cases
    print("\nTesting nearby development cases:")
    if result and 'location' in result:
        cases = get_nearby_cases(
            METRO["DEV_CASES"],
            lon=result["location"]["x"],
            lat=result["location"]["y"],
            meters=800,
            out_fields="CASE_NUMBER,CASE_TYPE,STATUS,PROJECT_NAME,ADDRESS,APPLICATION_DATE,STATUS_DATE"
        )
        if cases:
            print(f"Found {len(cases)} nearby development case(s):")
            for i, case in enumerate(cases[:5], 1):  # Show first 5 cases
                print(f"  {i}. {case.get('CASE_NUMBER')} - {case.get('CASE_TYPE')} - {case.get('PROJECT_NAME')}")
                print(f"     Status: {case.get('STATUS')}")
                print(f"     Address: {case.get('ADDRESS')}")
        else:
            print("No nearby development cases found")
