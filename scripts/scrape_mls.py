#!/usr/bin/env python3
"""Scrape the user-provided Matrix portal into normalized private-source JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parents[1]
SECTION_HEADERS = (
    "General Description",
    "Interior",
    "Exterior",
    "Additional Information",
)


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.action = ""
        self.hidden: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "form" and not self.action:
            self.action = html.unescape(attributes.get("action") or "")
        if (
            tag == "input"
            and (attributes.get("type") or "").lower() == "hidden"
            and attributes.get("name")
        ):
            self.hidden[attributes["name"]] = html.unescape(attributes.get("value") or "")


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip_depth = max(0, self.skip_depth - 1)

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value and not self.skip_depth:
            self.items.append(html.unescape(value))


def parse_form(body: str) -> FormParser:
    parser = FormParser()
    parser.feed(body)
    if not parser.action or "__VIEWSTATE" not in parser.hidden:
        raise ValueError("Matrix form or ViewState was not found")
    return parser


def unique_gallery_urls(body: str) -> list[str]:
    """Read the medium-size Type=1 gallery map while preserving image order."""
    decoded = html.unescape(body)
    candidates: list[tuple[int, str]] = []
    for match in re.finditer(
        r"""['"](\d+)_3['"]\s*:\s*['"]([^'"]+GetMedia\.ashx[^'"]+)['"]""",
        decoded,
        re.IGNORECASE,
    ):
        url = match.group(2)
        if "Type=1" in url and "Size=3" in url:
            candidates.append((int(match.group(1)), url))

    if not candidates:
        for match in re.finditer(
            r"""<img[^>]+class=["'][^"']*ivrImg[^"']*["'][^>]+src=["']([^"']+)["']""",
            decoded,
            re.IGNORECASE,
        ):
            url = match.group(1)
            if "GetMedia.ashx" in url and "Type=1" in url:
                candidates.append((len(candidates), url))

    output: list[str] = []
    for _, url in sorted(candidates, key=lambda pair: pair[0]):
        if url not in output:
            output.append(url)
    return output


def school_tail_pairs(values: list[str]) -> list[list[str]]:
    """Normalize Matrix's odd flattened school tail into explicit role/value pairs."""
    output: list[list[str]] = []
    index = 0
    while index < len(values):
        label = values[index]
        value = values[index + 1] if index + 1 < len(values) else ""
        if label in {"Elem", "Middle School", "High"}:
            district = ""
            if index + 2 < len(values) and values[index + 2].startswith("/"):
                district = values[index + 2]
                index += 1
            combined = value
            if district:
                combined = f"{combined} · {district}" if combined else district
            output.append([label, combined])
        elif label.startswith("/"):
            if output:
                output[-1][1] = f"{output[-1][1]} · {label}" if output[-1][1] else label
            else:
                output.append(["Elem", label])
        else:
            output.append([label, value])
        index += 2
    return output


def parse_sections(content: list[str]) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    positions = {header: content.index(header) for header in SECTION_HEADERS if header in content}
    for header in SECTION_HEADERS:
        if header not in positions:
            continue
        start = positions[header] + 1
        end = min(
            (position for position in positions.values() if position > positions[header]),
            default=len(content),
        )
        values = content[start:end]
        if header == "General Description" and "Elem" in values:
            school_start = values.index("Elem")
            regular = values[:school_start]
            if len(regular) % 2:
                raise ValueError(f"odd non-school field count in {header}: {len(regular)}")
            sections[header] = [
                [regular[index], regular[index + 1]] for index in range(0, len(regular), 2)
            ] + school_tail_pairs(values[school_start:])
            continue
        if len(values) % 2:
            raise ValueError(f"odd label/value count in {header}: {len(values)}")
        sections[header] = [
            [values[index], values[index + 1]] for index in range(0, len(values), 2)
        ]
    return sections


def field_value(sections: dict[str, list[list[str]]], label: str) -> str:
    for pairs in sections.values():
        for field_label, value in pairs:
            if field_label == label:
                return value
    return ""


def parse_detail(body: str, index: int, key: str) -> dict[str, object]:
    parser = VisibleTextParser()
    parser.feed(body)
    items = parser.items
    start = items.index("See Previous Results") + 1
    end = items.index("Notes for you and your agent")
    content = items[start:end]
    general_index = content.index("General Description")
    heading = content[:general_index]
    mls_label_index = heading.index("MLS#:")

    address = heading[0]
    city = heading[mls_label_index - 1]
    mls = heading[mls_label_index + 1]
    price = next(
        value for value in heading[mls_label_index + 2 :] if re.fullmatch(r"\$[\d,]+", value)
    )
    price_index = heading.index(price)
    status = next(
        (
            value
            for value in heading[price_index + 1 :]
            if value in {"Active", "Pending", "Contingent", "Sold"}
        ),
        heading[price_index + 1],
    )
    description_candidates = [
        value
        for value in heading[price_index + 1 :]
        if (
            len(value) >= 40
            and value not in {"Upcoming Open House Information"}
            and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value)
        )
    ]
    description = max(description_candidates, key=len, default="")
    sections = parse_sections(content)
    images = unique_gallery_urls(body)
    if not images:
        raise ValueError("no gallery images found")

    return {
        "index": index,
        "key": key,
        "address": address,
        "city": city,
        "mls": mls,
        "price": price,
        "status": status,
        "description": description,
        "description_vi": "",
        "bedrooms": field_value(sections, "Beds Total"),
        "bathrooms": field_value(sections, "Baths Total"),
        "full_baths": field_value(sections, "Baths Full"),
        "half_baths": field_value(sections, "Baths Half"),
        "sqft": field_value(sections, "Sq Ft Total"),
        "lot": field_value(sections, "Apprx Lot"),
        "year": field_value(sections, "Year Built"),
        "building_type": field_value(sections, "Building Type"),
        "sections": sections,
        "images": images,
        "sections_translated": {},
        "visible_text_count": len(items),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--link", type=Path, default=ROOT / "link.txt")
    parser.add_argument("--output", type=Path, default=ROOT / ".m" / "listings-raw.json")
    parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args()

    portal_url = args.link.read_text(encoding="utf-8").strip()
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0"
    parent = session.get(portal_url, timeout=45)
    parent.raise_for_status()
    form = parse_form(parent.text)
    keys = form.hidden.get("_ctl0$m_hfKeys", "").split(",")
    keys = [key for key in keys if key]
    view_match = re.search(r"Redisplay\|([^\"'<> \t]+?),,\d+", parent.text)
    if not view_match:
        raise SystemExit("Could not discover the Matrix detail view ID")
    view_id = html.unescape(view_match.group(1))
    post_url = urljoin(parent.url, form.action)

    listings: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for index, key in enumerate(keys):
        data = dict(form.hidden)
        data["__EVENTTARGET"] = "_ctl0$m_DisplayCore"
        data["__EVENTARGUMENT"] = f"Redisplay|{view_id},,{index}"
        try:
            response = session.post(post_url, data=data, timeout=75)
            response.raise_for_status()
            item = parse_detail(response.text, index, key)
            listings.append(item)
            fields = sum(len(values) for values in item["sections"].values())
            print(
                f"{index + 1:02}/{len(keys)} {item['mls']:<12} "
                f"imgs={len(item['images']):2} fields={fields:2} {item['address']}",
                flush=True,
            )
        except Exception as exc:
            errors.append({"index": index, "key": key, "error": repr(exc)})
            print(f"ERROR {index + 1:02}/{len(keys)} {type(exc).__name__}: {exc}", flush=True)
        time.sleep(args.delay)

    result = {
        "source": {
            "name": "MLSListings Matrix Portal",
            "listing_count": len(keys),
        },
        "listings": listings,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "expected": len(keys),
        "listings": len(listings),
        "errors": len(errors),
        "images": sum(len(item["images"]) for item in listings),
    }
    print(json.dumps(summary, ensure_ascii=False))
    if errors or len(listings) != len(keys):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
