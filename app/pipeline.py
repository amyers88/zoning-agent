from typing import Protocol, Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# ---------- Contracts ----------
@dataclass
class Parcel:
    parcel_id: str
    lot_area_sqft: int
    lot_area_acres: float
    frontage_ft: Optional[int]
    depth_ft: Optional[int]
    geometry_type: str
    centroid_lat: float
    centroid_lon: float

@dataclass
class Zoning:
    district: str
    subdistrict: Optional[str] = None

@dataclass
class Overlay:
    name: str
    type: str

# ---------- Protocols ----------
class ParcelFetcher(Protocol):
    def by_address(self, address: str) -> Parcel: ...

class ZoningFetcher(Protocol):
    def for_parcel(self, parcel: Parcel) -> Zoning: ...

class OverlayFetcher(Protocol):
    def for_parcel(self, parcel: Parcel) -> List[Overlay]: ...

class StandardsStore(Protocol):
    def for_zoning(self, zoning: Zoning) -> Dict[str, Any]: ...

# ---------- Stubs (replace later with real GIS / RAG) ----------
class StubParcelFetcher:
    def by_address(self, address: str) -> Parcel:
        # TODO: replace with Metro ArcGIS call
        return Parcel(
            parcel_id="stub-123",
            lot_area_sqft=19166,
            lot_area_acres=0.44,
            frontage_ft=None,
            depth_ft=None,
            geometry_type="Polygon",
            centroid_lat=36.1627,
            centroid_lon=-86.7816,
        )

class StubZoningFetcher:
    def for_parcel(self, parcel: Parcel) -> Zoning:
        # TODO: replace with zoning layer intersect
        return Zoning(district="DTC", subdistrict="Core")

class StubOverlayFetcher:
    def for_parcel(self, parcel: Parcel) -> List[Overlay]:
        # TODO: replace with overlay layer intersects
        return [Overlay(name="Downtown Code UDO", type="Design")]

class JSONStandardsStore:
    """Load curated Title 17 tables from /data/standards/*.json"""
    def __init__(self, table: Dict[str, Dict[str, Any]]):
        self.table = table

    def for_zoning(self, zoning: Zoning) -> Dict[str, Any]:
        key = zoning.district.upper()
        return self.table.get(key, {
            "height_max_stories": None,
            "height_max_feet": None,
            "far_base": None,
            "far_bonus_max": None,
            "setbacks_ft": {"front": None, "side": None, "rear": None},
            "lot_coverage_max_pct": None,
            "open_space_min_pct": None,
            "uses": {"by_right": [], "conditional": [], "prohibited": []},
            "parking": {"ratios": [], "reductions": [], "structured_required": None},
            "bonus_programs": [],
            "process": {
                "by_right": None, "conditional_use": None,
                "variance": None, "rezoning": None,
                "typical_timeline_days": {"variance": None}
            },
            "citations": []
        })

# ---------- Orchestrator ----------
def assemble_report_json(address: str,
                         parcel_fetcher: ParcelFetcher,
                         zoning_fetcher: ZoningFetcher,
                         overlay_fetcher: OverlayFetcher,
                         standards_store: StandardsStore) -> Dict[str, Any]:
    parcel = parcel_fetcher.by_address(address)
    zoning = zoning_fetcher.for_parcel(parcel)
    overlays = overlay_fetcher.for_parcel(parcel)

    standards = standards_store.for_zoning(zoning)

    report = {
        "address": address,
        "jurisdiction": "Metro Nashville–Davidson County",
        "parcel": asdict(parcel),
        "zoning": {"district": zoning.district, "subdistrict": zoning.subdistrict},
        "overlays": [asdict(o) for o in overlays],
        "standards": {
            "height_max_stories": standards.get("height_max_stories"),
            "height_max_feet": standards.get("height_max_feet"),
            "far_base": standards.get("far_base"),
            "far_bonus_max": standards.get("far_bonus_max"),
            "setbacks_ft": standards.get("setbacks_ft", {"front": None, "side": None, "rear": None}),
            "lot_coverage_max_pct": standards.get("lot_coverage_max_pct"),
            "open_space_min_pct": standards.get("open_space_min_pct"),
        },
        "uses": standards.get("uses", {"by_right": [], "conditional": [], "prohibited": []}),
        "parking": standards.get("parking", {"ratios": [], "reductions": [], "structured_required": None}),
        "bonus_programs": standards.get("bonus_programs", []),
        "process": standards.get("process", {
            "by_right": None, "conditional_use": None, "variance": None, "rezoning": None,
            "typical_timeline_days": {"variance": None}
        }),
        "citations": standards.get("citations", []),
        "feasibility_summary": []
    }
    return report

if __name__ == "__main__":
    # Minimal DTC example table (fill out over time)
    standards_table = {
        "DTC": {
            "height_max_stories": 30,
            "height_max_feet": 400,
            "far_base": None,
            "far_bonus_max": None,
            "setbacks_ft": {"front": 0, "side": 0, "rear": 0},
            "uses": {
                "by_right": ["Retail", "Office", "Residential", "Hotel", "Entertainment"],
                "conditional": ["Assembly"],
                "prohibited": ["Heavy Industrial"]
            },
            "parking": {
                "ratios": ["DTC core often exempt; see §17.20"],
                "reductions": ["Near transit, shared parking provisions"],
                "structured_required": None
            },
            "bonus_programs": [
                {"name": "Public Amenities / Art", "benefit": "Bonus height", "citation": "DTC Bonus Chart §..."}
            ],
            "process": {
                "by_right": "Administrative (Planning staff)",
                "conditional_use": "BZA",
                "variance": "BZA",
                "rezoning": "Metro Council",
                "typical_timeline_days": {"variance": 60}
            },
            "citations": [
                {"title": "Metro Code Title 17 – DTC", "section": "§17.xx.xxx", "url": ""},
                {"title": "Parking Standards", "section": "§17.20", "url": ""}
            ]
        }
    }

    report = assemble_report_json(
        address="100 Broadway, Nashville, TN",
        parcel_fetcher=StubParcelFetcher(),
        zoning_fetcher=StubZoningFetcher(),
        overlay_fetcher=StubOverlayFetcher(),
        standards_store=JSONStandardsStore(standards_table)
    )
    # At this point, send `report` + the Renderer Prompt to Windsurf to produce the formatted output.
    print(report)
