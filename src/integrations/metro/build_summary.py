"""
Summary builder for Metro Nashville zoning analysis.

This module provides functions to generate a summary of zoning analysis results
in a structured format for display in the UI.
"""

from typing import Dict, Any, Optional, List


def _lot_area_sqft(parcel_attrs: Dict[str, Any]) -> Optional[float]:
    """
    Calculate lot area in square feet from parcel attributes.
    
    Args:
        parcel_attrs: Dictionary of parcel attributes
        
    Returns:
        Lot area in square feet, or None if not available
    """
    # Try common fields first; fall back to acres * 43560 if present
    if "Acres" in parcel_attrs and isinstance(parcel_attrs["Acres"], (int, float)):
        return float(parcel_attrs["Acres"]) * 43560.0
    if "DeededAcreage" in parcel_attrs and isinstance(parcel_attrs["DeededAcreage"], (int, float)):
        return float(parcel_attrs["DeededAcreage"]) * 43560.0
    return None


def _overlay_flags(overlays_attrs):
    """
    Process overlay information and generate flags for important overlays.
    
    Args:
        overlays_attrs: List of overlay attributes
        
    Returns:
        Dictionary with 'overlays' and 'flags' keys
    """
    names = []
    for o in overlays_attrs or []:
        label = o.get("ZONINGNAME") or o.get("OVERLAY_NAME") or o.get("NAME") or o.get("ZONING") or "Overlay"
        code = o.get("ZONING") or o.get("CODE") or ""
        names.append(code or label)
    # flag a few common constraints
    flags = []
    joined = " ".join(n.upper() for n in names)
    if "HIST" in joined or "CONSERVATION" in joined or "NC" in joined:
        flags.append("Historic/Conservation review likely")
    return {"overlays": names, "flags": flags}


def build_summary_stub(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of zoning analysis results.
    
    Args:
        analysis: Full analysis dictionary from analyze_property()
        
    Returns:
        Dictionary with summary information for display in the UI
    """
    parcel_attrs = (analysis.get("parcel") or {}).get("attributes") or {}
    zoning_base = analysis.get("zoning", {}).get("base") or {}
    overlays = analysis.get("zoning", {}).get("overlays") or []
    flood_approved = analysis.get("constraints", {}).get("flood_approved") or []

    lot_sqft = _lot_area_sqft(parcel_attrs)
    lot_acres = round(lot_sqft / 43560.0, 3) if lot_sqft else None

    base_code = None
    if isinstance(zoning_base, dict):
        # Try common field names; adjust once you inspect actual attributes
        base_code = zoning_base.get("ZONE_CODE") or zoning_base.get("ZONE") or zoning_base.get("BASE_ZONE") or zoning_base.get("DISTRICT")

    overlay_info = _overlay_flags(overlays)

    # Flood quick flag
    flood_flags = []
    for f in flood_approved:
        z = (f.get("FloodZone") or f.get("FLOODZONE") or "").upper()
        if z in ("AE", "A", "VE", "FW"):  # Special Flood Hazard Areas
            flood_flags.append(f"Flood Zone {z}")
    if flood_flags:
        overlay_info["flags"].extend(flood_flags)

    # DTC special case
    if base_code and str(base_code).upper().startswith("DTC"):
        return {
            "district": base_code,
            "lot_area_sqft": lot_sqft,
            "lot_area_acres": lot_acres,
            "by_right": {
                "note": "Downtown Code parcel — height/form depend on sub-district. See DTC PDF.",
                "max_height_ft": None,
                "indicative_far": None,
                "frontage": "See sub-district table",
                "parking_basis": "DTC-specific; often reduced/waived in core areas"
            },
            "bonuses_available": ["Bonus height program (see DTC)"],
            "flags": overlay_info["flags"],
            "overlays": overlay_info["overlays"]
        }

    # Non-DTC conservative stub
    return {
        "district": base_code,
        "lot_area_sqft": lot_sqft,
        "lot_area_acres": lot_acres,
        "by_right": {
            "max_height_ft": None,     # fill later per district table
            "indicative_far": None,    # fill later per district table
            "parking_basis": "Per base district; subject to use/type"
        },
        "bonuses_available": [],
        "flags": overlay_info["flags"],
        "overlays": overlay_info["overlays"]
    }
