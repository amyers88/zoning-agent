"""
Metro Nashville GIS API endpoints and configuration.

This module contains all the necessary endpoints for interacting with Metro Nashville's
GIS services, including parcel data, zoning information, flood zones, and development cases.
"""

# Base URL for Metro Nashville ArcGIS REST services
BASE_URL = "https://maps.nashville.gov/arcgis/rest/services"

# Endpoint configuration
METRO = {
    # Geocoding service for address lookup
    "GEOCODER": "https://maps.nashville.gov/arcgis2/rest/services/Locators/NashCompLocator/GeocodeServer",
    
    # Parcel data
    "PARCELS": f"{BASE_URL}/Cadastral/Parcels/MapServer/0",
    
    # Zoning information
    "BASE_ZONING": f"{BASE_URL}/Zoning_Landuse/BaseZoning/MapServer/0",
    "ZONING_OVERLAYS": f"{BASE_URL}/Zoning_Landuse/Zoning_Overlay_Districts/MapServer/0",
    
    # Flood zones
    "FEMA_APPROVED": f"{BASE_URL}/Hydrography/FEMA_FloodHazardAreas/MapServer/0",
    "FEMA_PENDING": f"{BASE_URL}/Hydrography/FEMA_FloodHazardAreas/MapServer/1",
    
    # Development tracking
    "DEV_CASES": f"{BASE_URL}/Planning/DevTracker_Cases/FeatureServer/0",
    
    # Documentation
    "DTC_PDF": "https://www.nashville.gov/sites/default/files/2025-06/Downtown-Code-250520.pdf?ct=1749150062"
}
