#!/usr/bin/env python3
"""Download all MLS gallery images to stable local paths and verify JPEGs."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]


def valid_jpeg(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 1000:
        return False
    with path.open("rb") as stream:
        start = stream.read(2)
        stream.seek(-2, os.SEEK_END)
        end = stream.read(2)
    return start == b"\xff\xd8" and end == b"\xff\xd9"


def download(job: tuple[str, Path], attempts: int = 4) -> tuple[Path, str, int]:
    url, destination = job
    if valid_jpeg(destination):
        return destination, "cached", destination.stat().st_size
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        temporary = destination.with_suffix(".part")
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=45,
            )
            response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/"):
                raise ValueError("response is not an image")
            temporary.write_bytes(response.content)
            if not valid_jpeg(temporary):
                raise ValueError("downloaded file is not a complete JPEG")
            os.replace(temporary, destination)
            return destination, "downloaded", len(response.content)
        except Exception as exc:
            temporary.unlink(missing_ok=True)
            if attempt == attempts - 1:
                return destination, f"error: {exc}", 0
            time.sleep(attempt + 1)
    return destination, "error", 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    listings = json.loads(args.source.read_text(encoding="utf-8"))["listings"]
    jobs: list[tuple[str, Path]] = []
    for item in listings:
        folder = ROOT / "assets" / "properties" / item["mls"].lower()
        for number, url in enumerate(item["images"], 1):
            jobs.append((url, folder / f"{number:03d}.jpg"))

    completed = errors = bytes_processed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        for destination, status, size in executor.map(download, jobs):
            completed += 1
            bytes_processed += size
            if status.startswith("error"):
                errors += 1
                print(f"ERROR {destination}: {status}", flush=True)
            elif completed % 100 == 0 or completed == len(jobs):
                print(
                    f"{completed}/{len(jobs)} images · "
                    f"{bytes_processed / 1024 / 1024:.1f} MB processed",
                    flush=True,
                )
    if errors:
        raise SystemExit(f"{errors} image downloads failed")
    print(f"Downloaded or verified {len(jobs)} images")


if __name__ == "__main__":
    main()

