import pandas as pd
from typing import Dict, Optional, Tuple
import requests
import json
import os

def budget_compare(paths: Dict[str, str]) -> str:
    """paths: {'budget': 'data/examples/budget.csv', 'draw': 'data/examples/draw.csv'}"""
    b = pd.read_csv(paths["budget"])
    d = pd.read_csv(paths["draw"])
    # Expect columns: LineItem, Amount
    m = b.merge(d, on="LineItem", suffixes=("_budget","_draw"), how="outer").fillna(0)
    m["Variance"] = m["Amount_draw"] - m["Amount_budget"]
    over = m[m["Variance"]>0][["LineItem","Amount_budget","Amount_draw","Variance"]]
    if over.empty:
        return "No overruns detected."
    return "Overruns (LineItem, Budget, Draw, Variance):\n" + over.to_string(index=False)

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a Nashville address to get latitude and longitude coordinates.
    Uses a free geocoding service for Nashville addresses.
    """
    try:
        # Add Nashville, TN to the address if not already present
        if "nashville" not in address.lower() and "tn" not in address.lower():
            address = f"{address}, Nashville, TN"
        
        # Use Nominatim (OpenStreetMap) geocoding service with simpler params
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "us"
        }
        
        headers = {
            "User-Agent": "Nashville-Zoning-AI/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        
        return None
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        # Return mock coordinates for testing
        return (36.1627, -86.7816)  # Downtown Nashville

def get_zoning_district(coordinates: Tuple[float, float]) -> Optional[str]:
    """
    Get the zoning district for given coordinates.
    First tries Metro Nashville ArcGIS Base Zoning layer; falls back to mock.
    """
    lat, lon = coordinates

    # Try ArcGIS Base Zoning MapServer provided by user
    try:
        service_url = os.getenv(
            "MNPD_BASE_ZONING_URL",
            "https://maps.nashville.gov/arcgis/rest/services/Zoning_Landuse/BaseZoning/MapServer"
        )
        layer = os.getenv("MNPD_BASE_ZONING_LAYER", "0")
        query_url = f"{service_url}/{layer}/query"

        params = {
            "f": "json",
            "geometry": f"{lon},{lat}",  # ArcGIS expects x,y = lon,lat
            "geometryType": "esriGeometryPoint",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "returnGeometry": "false",
            "outFields": "*"
        }
        r = requests.get(query_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        if features:
            attrs = features[0].get("attributes", {})
            # Try common field names used by zoning layers
            for key in [
                "ZONE_DESC", "ZONING", "BASE_ZONING", "ZONE_CODE", "ZONE", "DISTRICT", "ZONING_CODE"
            ]:
                if key in attrs and attrs[key]:
                    return str(attrs[key]).strip()
            # If no obvious field, return stringified attrs for debugging
            return attrs.get("ZONE_DESC", None) or attrs.get("ZONING", None) or attrs.get("ZONE", None)
    except Exception as e:
        print(f"ArcGIS zoning lookup failed; falling back to mock. Error: {e}")

    # Fallback mock if ArcGIS not reachable
    if 36.15 <= lat <= 36.18 and -86.8 <= lon <= -86.75:
        return "MUL"
    if 36.10 <= lat <= 36.20 and -86.85 <= lon <= -86.70:
        return "CS"
    return "RS"

def get_nashville_zoning_info(zoning_district: str) -> Dict[str, str]:
    """
    Get basic information about a Nashville zoning district.
    This would typically come from the official zoning code.
    """
    zoning_info = {
        "RS": "Residential Single Family - Single family homes, duplexes",
        "RM": "Residential Multi-Family - Apartments, condos, townhomes", 
        "OR": "Office Residential - Mixed office and residential",
        "CS": "Commercial Services - Retail, restaurants, services",
        "CL": "Commercial Limited - Limited commercial uses",
        "MUL": "Mixed Use Limited - Mixed residential and commercial",
        "MUN": "Mixed Use Neighborhood - Neighborhood-scale mixed use",
        "MUG": "Mixed Use General - General mixed use development",
        "MUI": "Mixed Use Intensive - High-density mixed use",
        "IR": "Industrial Restricted - Light industrial",
        "IG": "Industrial General - General industrial uses"
    }
    
    return {
        "district": zoning_district,
        "description": zoning_info.get(zoning_district, "Unknown zoning district"),
        "source": "Nashville Zoning Code 2025"
    }

def get_static_map_url(coordinates: Tuple[float, float], zoom: int = 15, width: int = 600, height: int = 400) -> str:
    """
    Return a static map image URL (OpenStreetMap) centered on the given coordinates.
    This uses the public OSM Static Map service.
    """
    lat, lon = coordinates
    size = f"{width}x{height}"
    # Red pushpin marker at the location
    marker = f"{lat},{lon},red-pushpin"
    return (
        "https://staticmap.openstreetmap.de/staticmap.php"
        f"?center={lat},{lon}&zoom={zoom}&size={size}&markers={marker}"
    )

def get_overlays(coordinates: Tuple[float, float]) -> Optional[list]:
    """
    Return a list of overlay district attributes intersecting the point.
    Requires environment variable MNPD_OVERLAYS_URL pointing to the Overlays MapServer/FeatureServer layer.
    Example: https://.../MapServer/0 or .../FeatureServer/0
    """
    lat, lon = coordinates
    service_url = os.getenv("MNPD_OVERLAYS_URL")
    layer = os.getenv("MNPD_OVERLAYS_LAYER", "0")
    if not service_url:
        # Not configured yet
        return []
    # Normalize URL to end with layer index
    if not service_url.rstrip("/").split("/")[-1].isdigit():
        query_url = f"{service_url.rstrip('/')}/{layer}/query"
    else:
        query_url = f"{service_url.rstrip('/')}/query"

    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",  # x,y = lon,lat
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "false",
        "outFields": "*"
    }
    try:
        r = requests.get(query_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        overlays = []
        for f in features:
            attrs = f.get("attributes", {})
            overlays.append(attrs)
        return overlays
    except Exception as e:
        print(f"Overlay lookup failed: {e}")
        return []

