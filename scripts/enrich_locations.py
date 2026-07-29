#!/usr/bin/env python3
"""Build static location insights from Census geocodes and OpenStreetMap data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EARTH_RADIUS_MILES = 3958.7613

THRESHOLDS_MILES = {
    "strict": {
        "vietnamese_community": 4.0,
        "lake": 2.0,
        "coast": 18.0,
        "highway": 0.5,
        "park": 0.25,
        "shopping": 0.5,
        "transit": 0.75,
    },
    "balanced": {
        "vietnamese_community": 6.0,
        "lake": 4.0,
        "coast": 22.0,
        "highway": 1.25,
        "park": 0.75,
        "shopping": 0.75,
        "transit": 1.25,
    },
    "broad": {
        "vietnamese_community": 10.0,
        "lake": 8.0,
        "coast": 30.0,
        "highway": 2.0,
        "park": 1.0,
        "shopping": 1.5,
        "transit": 2.0,
    },
}

RESTAURANT_RADII = {"strict": 0.5, "balanced": 1.0, "broad": 2.0}
RESTAURANT_MIN_COUNTS = {"strict": 3, "balanced": 5, "broad": 5}

VIETNAMESE_COMMUNITY_ANCHORS = [
    {
        "name": "Little Saigon / Grand Century Mall",
        "lat": 37.3333744,
        "lon": -121.8568767,
    },
    {
        "name": "The Shops at Vietnam Town",
        "lat": 37.3320927,
        "lon": -121.8582737,
    },
    {
        "name": "Trung tâm Văn hóa Việt-Mỹ",
        "lat": 37.3177577,
        "lon": -121.8445645,
    },
    {
        "name": "Vietnamese Heritage Garden",
        "lat": 37.3253852,
        "lon": -121.8560794,
    },
]

COAST_ANCHORS = [
    {"name": "Santa Cruz Main Beach", "lat": 36.9628352, "lon": -122.0214682},
    {"name": "Natural Bridges State Beach", "lat": 36.9520839, "lon": -122.0571253},
    {"name": "New Brighton State Beach", "lat": 36.9793072, "lon": -121.9264964},
    {"name": "Capitola Beach", "lat": 36.9713981, "lon": -121.9516469},
    {"name": "Half Moon Bay State Beach", "lat": 37.4784919, "lon": -122.4493970},
]

SIGNIFICANT_WATER_ANCHORS = [
    {"name": "Almaden Lake", "lat": 37.2411676, "lon": -121.8715318},
    {"name": "Lake Cunningham", "lat": 37.3359213, "lon": -121.8085},
    {"name": "Chesbro Reservoir", "lat": 37.121076, "lon": -121.7099831},
    {"name": "Anderson Reservoir", "lat": 37.1730923, "lon": -121.6142053},
    {"name": "Calero Reservoir", "lat": 37.1806342, "lon": -121.7809079},
    {"name": "Coyote Lake", "lat": 37.0042712, "lon": -121.6294743},
    {"name": "Uvas Reservoir", "lat": 37.077204, "lon": -121.7037452},
    {"name": "Vasona Reservoir", "lat": 37.2429214, "lon": -121.9673707},
    {"name": "Lexington Reservoir", "lat": 37.1873171, "lon": -121.9912366},
    {"name": "Guadalupe Reservoir", "lat": 37.1928664, "lon": -121.8756171},
]

# Three new-development addresses are not represented as exact Census points yet.
COORDINATE_OVERRIDES = {
    4: {
        "lat": 37.1310960,
        "lon": -121.6771151,
        "precision": "street",
        "source": "OpenStreetMap street centroid",
    },
    9: {
        "lat": 37.1594674,
        "lon": -121.6309306,
        "precision": "approximate_street",
        "source": "OpenStreetMap Borello Ranch street approximation",
    },
    10: {
        "lat": 37.1611245,
        "lon": -121.6362307,
        "precision": "street",
        "source": "OpenStreetMap street centroid",
    },
}

CATEGORY_LABELS = {
    "vietnamese_community": "Khu thương mại / sinh hoạt cộng đồng Việt",
    "lake": "Hồ hoặc hồ chứa nước",
    "coast": "Bãi biển",
    "highway": "Cao tốc",
    "park": "Công viên",
    "restaurants": "Nhà hàng",
    "shopping": "Mua sắm",
    "transit": "Ga đường sắt / giao thông công cộng",
}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(value))


def local_xy(lat: float, lon: float, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    x = math.radians(lon - origin_lon) * math.cos(math.radians(origin_lat)) * EARTH_RADIUS_MILES
    y = math.radians(lat - origin_lat) * EARTH_RADIUS_MILES
    return x, y


def point_segment_distance_miles(
    lat: float,
    lon: float,
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    ax, ay = local_xy(start[0], start[1], lat, lon)
    bx, by = local_xy(end[0], end[1], lat, lon)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(ax, ay)
    scalar = max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + scalar * dx, ay + scalar * dy)


def element_point(element: dict) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if center:
        return float(center["lat"]), float(center["lon"])
    return None


def normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def dedupe_points(points: list[dict]) -> list[dict]:
    output: list[dict] = []
    buckets: dict[str, list[dict]] = defaultdict(list)
    for point in points:
        key = normalized_name(point["name"])
        duplicate = any(
            haversine_miles(point["lat"], point["lon"], item["lat"], item["lon"]) < 0.08
            for item in buckets[key]
        )
        if not duplicate:
            buckets[key].append(point)
            output.append(point)
    return output


def load_geocodes(path: Path) -> dict[int, dict]:
    output: dict[int, dict] = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.reader(stream):
            index = int(row[0])
            if len(row) >= 6 and row[2] == "Match":
                lon_text, lat_text = row[5].split(",")
                output[index] = {
                    "lat": float(lat_text),
                    "lon": float(lon_text),
                    "precision": "address" if row[3] == "Exact" else "address_range",
                    "source": "U.S. Census Geocoder",
                    "matched_address": row[4],
                }
    output.update(COORDINATE_OVERRIDES)
    return output


def load_pois(path: Path) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    data = json.loads(path.read_text(encoding="utf-8"))["elements"]
    for element in data:
        tags = element.get("tags", {})
        name = tags.get("name")
        point = element_point(element)
        if not name or not point:
            continue
        record = {"name": name, "lat": point[0], "lon": point[1]}
        if tags.get("amenity") == "restaurant":
            groups["restaurants"].append(record)
        if tags.get("leisure") == "park":
            groups["park"].append(record)
        if tags.get("shop") in {"supermarket", "mall", "department_store"}:
            groups["shopping"].append(record)
        if tags.get("natural") == "water" or tags.get("water") in {"lake", "reservoir"}:
            groups["lake"].append(record)
    return {key: dedupe_points(values) for key, values in groups.items()}


def load_transit(path: Path) -> list[dict]:
    records = []
    for element in json.loads(path.read_text(encoding="utf-8"))["elements"]:
        tags = element.get("tags", {})
        point = element_point(element)
        name = tags.get("name")
        if not name or not point:
            continue
        network = tags.get("network") or tags.get("operator") or ""
        records.append(
            {
                "name": f"{name} · {network}" if network and network not in name else name,
                "lat": point[0],
                "lon": point[1],
            }
        )
    return dedupe_points(records)


def highway_label(tags: dict) -> str:
    reference = tags.get("ref", "").replace(";", " / ")
    name = tags.get("name", "")
    if reference:
        return reference
    return name or "Cao tốc gần nhất"


def load_highway_segments(paths: list[Path]) -> list[dict]:
    segments: list[dict] = []
    seen = set()
    for path in paths:
        for element in json.loads(path.read_text(encoding="utf-8"))["elements"]:
            if element.get("tags", {}).get("highway") != "motorway":
                continue
            geometry = element.get("geometry", [])
            label = highway_label(element.get("tags", {}))
            for start, end in zip(geometry, geometry[1:]):
                key = (
                    round(start["lat"], 6),
                    round(start["lon"], 6),
                    round(end["lat"], 6),
                    round(end["lon"], 6),
                    label,
                )
                if key in seen:
                    continue
                seen.add(key)
                segments.append(
                    {
                        "name": label,
                        "start": (float(start["lat"]), float(start["lon"])),
                        "end": (float(end["lat"]), float(end["lon"])),
                    }
                )
    return segments


def nearest_point(lat: float, lon: float, points: list[dict]) -> dict:
    nearest = min(
        points,
        key=lambda item: haversine_miles(lat, lon, item["lat"], item["lon"]),
    )
    return {
        "name": nearest["name"],
        "distance_miles": round(
            haversine_miles(lat, lon, nearest["lat"], nearest["lon"]),
            2,
        ),
    }


def nearby_counts(lat: float, lon: float, points: list[dict]) -> dict[str, int]:
    distances = [haversine_miles(lat, lon, item["lat"], item["lon"]) for item in points]
    return {
        "0.5": sum(distance <= 0.5 for distance in distances),
        "1": sum(distance <= 1.0 for distance in distances),
        "2": sum(distance <= 2.0 for distance in distances),
    }


def nearest_highway(lat: float, lon: float, segments: list[dict]) -> dict:
    nearest = min(
        segments,
        key=lambda item: point_segment_distance_miles(
            lat, lon, item["start"], item["end"]
        ),
    )
    return {
        "name": nearest["name"],
        "distance_miles": round(
            point_segment_distance_miles(lat, lon, nearest["start"], nearest["end"]),
            2,
        ),
    }


def evidence_from_description(listing: dict) -> list[str]:
    text = f"{listing.get('description', '')} {listing.get('description_vi', '')}"
    rules = [
        ("park", r"\bpark\b|công viên"),
        ("restaurants", r"\bdining\b|\brestaurants?\b|ăn uống|nhà hàng"),
        ("shopping", r"\bshopping\b|\bshops?\b|\bmall\b|mua sắm|cửa hàng"),
        ("highway", r"\bfreeways?\b|\bhighways?\b|cao tốc|xa lộ|commute routes"),
        ("lake", r"\blake\b|\breservoir\b|hồ chứa|hồ nước"),
        ("transit", r"\bBART\b|\bCaltrain\b|\blight rail\b|đường sắt|ga "),
        ("park", r"\btrail\b|đường mòn"),
    ]
    found = []
    for category, pattern in rules:
        if category not in found and re.search(pattern, text, re.IGNORECASE):
            found.append(category)
    return found


def match_flags(amenities: dict) -> dict[str, dict[str, bool]]:
    output = {}
    for mode in ("strict", "balanced", "broad"):
        flags = {}
        for category, threshold in THRESHOLDS_MILES[mode].items():
            flags[category] = amenities[category]["distance_miles"] <= threshold
        count_key = str(RESTAURANT_RADII[mode]).rstrip("0").rstrip(".")
        flags["restaurants"] = (
            amenities["restaurants"]["counts"].get(count_key, 0)
            >= RESTAURANT_MIN_COUNTS[mode]
        )
        output[mode] = flags
    return output


def location_summary(amenities: dict, flags: dict) -> str:
    highlights = []
    preferred_order = [
        "vietnamese_community",
        "park",
        "restaurants",
        "shopping",
        "highway",
        "transit",
        "lake",
        "coast",
    ]
    for category in preferred_order:
        if not flags["balanced"][category]:
            continue
        detail = amenities[category]
        if category == "restaurants":
            highlights.append(f"{detail['counts']['1']} nhà hàng trong 1 dặm")
        else:
            highlights.append(
                f"{CATEGORY_LABELS[category].lower()} cách khoảng "
                f"{detail['distance_miles']:.1f} dặm"
            )
        if len(highlights) == 3:
            break
    if not highlights:
        return "Vị trí ngoại ô; các tiện ích chính cần di chuyển xa hơn."
    return " · ".join(highlights)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        default=ROOT / "data" / "listings-source.json",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=ROOT / ".m" / "location",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "location-insights.json",
    )
    parser.add_argument("--snapshot-date", default="2026-07-29")
    args = parser.parse_args()

    listings = json.loads(args.source.read_text(encoding="utf-8"))["listings"]
    geocodes = load_geocodes(args.cache_dir / "census-output.csv")
    if len(geocodes) != len(listings):
        missing = sorted(set(range(len(listings))) - set(geocodes))
        raise SystemExit(f"Missing geocodes: {missing}")

    pois = load_pois(args.cache_dir / "osm-pois.json")
    pois["transit"] = load_transit(args.cache_dir / "osm-transit.json")
    highway_segments = load_highway_segments(
        [
            args.cache_dir / "roads-north.json",
            args.cache_dir / "roads-west.json",
            args.cache_dir / "roads-east.json",
            args.cache_dir / "roads-south.json",
        ]
    )

    insights = {}
    for listing in listings:
        index = int(listing["index"])
        location = geocodes[index]
        lat, lon = location["lat"], location["lon"]
        amenities = {
            "vietnamese_community": nearest_point(
                lat, lon, VIETNAMESE_COMMUNITY_ANCHORS
            ),
            "lake": nearest_point(lat, lon, SIGNIFICANT_WATER_ANCHORS),
            "coast": nearest_point(lat, lon, COAST_ANCHORS),
            "highway": nearest_highway(lat, lon, highway_segments),
            "park": nearest_point(lat, lon, pois["park"]),
            "restaurants": nearest_point(lat, lon, pois["restaurants"]),
            "shopping": nearest_point(lat, lon, pois["shopping"]),
            "transit": nearest_point(lat, lon, pois["transit"]),
        }
        for category in ("park", "restaurants", "shopping"):
            amenities[category]["counts"] = nearby_counts(lat, lon, pois[category])
        flags = match_flags(amenities)
        insights[listing["mls"]] = {
            "geocode": {
                "precision": location["precision"],
                "source": location["source"],
            },
            "amenities": amenities,
            "matches": flags,
            "location_summary_vi": location_summary(amenities, flags),
            "mls_evidence_categories": evidence_from_description(listing),
        }
        balanced = [name for name, value in flags["balanced"].items() if value]
        print(
            f"{index + 1:02}/{len(listings)} {listing['mls']:<12} "
            f"community={amenities['vietnamese_community']['distance_miles']:>5.1f} "
            f"park={amenities['park']['distance_miles']:>4.1f} "
            f"restaurants={amenities['restaurants']['counts']['1']:>2} "
            f"balanced={','.join(balanced) or '-'}"
        )

    output = {
        "snapshot_date": args.snapshot_date,
        "methodology": {
            "distance_type": "straight_line",
            "distance_unit": "miles",
            "thresholds_miles": THRESHOLDS_MILES,
            "restaurant_radii_miles": RESTAURANT_RADII,
            "restaurant_min_counts": RESTAURANT_MIN_COUNTS,
            "notes_vi": (
                "Khoảng cách là đường chim bay, không phải thời gian lái xe. "
                "Khu người Việt được đo tới các trung tâm thương mại, văn hóa và "
                "sinh hoạt cộng đồng Việt công khai; không suy đoán sắc tộc cư dân."
            ),
            "sources": [
                "U.S. Census Geocoder (MAF/TIGER)",
                "OpenStreetMap contributors (ODbL)",
                "City of San José public Vietnamese community locations",
            ],
        },
        "category_labels": CATEGORY_LABELS,
        "listings": insights,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(insights)} location insight records to {args.output}")


if __name__ == "__main__":
    main()
