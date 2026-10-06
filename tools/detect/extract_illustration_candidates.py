"""Find large ink regions on rendered pages and save traceable crop candidates.

This is a conservative computer-vision prefilter, not a semantic classifier.
All crops remain lossless PNGs and point back to their page and PDF location.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGE_INDEX = PROJECT_ROOT / "metadata" / "pages.jsonl"
OUTPUT_INDEX = PROJECT_ROOT / "metadata" / "illustrations.jsonl"
PAGE_REVIEW = PROJECT_ROOT / "metadata" / "visual_review.jsonl"
DETECTOR_WIDTH = 400


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def unite_nearby(boxes: list[tuple[int, int, int, int]], gap: int) -> list[tuple[int, int, int, int]]:
    """Merge overlapping or nearby components, repeatedly until stable."""
    current = list(boxes)
    changed = True
    while changed:
        changed = False
        merged: list[tuple[int, int, int, int]] = []
        while current:
            x0, y0, x1, y1 = current.pop()
            rest = []
            for ax0, ay0, ax1, ay1 in current:
                separated = x1 + gap < ax0 or ax1 + gap < x0 or y1 + gap < ay0 or ay1 + gap < y0
                if separated:
                    rest.append((ax0, ay0, ax1, ay1))
                else:
                    x0, y0, x1, y1 = min(x0, ax0), min(y0, ay0), max(x1, ax1), max(y1, ay1)
                    changed = True
            merged.append((x0, y0, x1, y1))
            current = rest
        current = merged
    return sorted(current, key=lambda box: (box[1], box[0]))


def find_regions(image: np.ndarray, min_area_fraction: float) -> tuple[list[tuple[int, int, int, int]], dict[str, float]]:
    height, width = image.shape[:2]
    small_height = max(1, round(DETECTOR_WIDTH * height / width))
    small = cv2.resize(image, (DETECTOR_WIDTH, small_height), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Scanner borders and isolated page-edge marks should not create a crop.
    margin_x = max(2, round(DETECTOR_WIDTH * 0.012))
    margin_y = max(2, round(small_height * 0.012))
    ink[:margin_y, :] = 0
    ink[-margin_y:, :] = 0
    ink[:, :margin_x] = 0
    ink[:, -margin_x:] = 0

    joined = cv2.morphologyEx(
        ink,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
    )
    count, _, stats, _ = cv2.connectedComponentsWithStats(joined, connectivity=8)
    total_area = float(DETECTOR_WIDTH * small_height)
    boxes: list[tuple[int, int, int, int]] = []
    for label in range(1, count):
        x, y, box_width, box_height, area = (int(value) for value in stats[label])
        box_area = max(1, box_width * box_height)
        fill = area / box_area
        area_fraction = area / total_area
        if area < max(1400, round(total_area * min_area_fraction)):
            continue
        if box_width < round(DETECTOR_WIDTH * 0.055) or box_height < round(small_height * 0.025):
            continue
        if fill < 0.018:
            continue
        boxes.append((x, y, x + box_width, y + box_height))

    # Join nearby pieces of the same drawing but keep separate chapter vignettes.
    boxes = unite_nearby(boxes, gap=8)
    edge_density = float(cv2.Canny(gray, 45, 135).mean() / 255.0)
    ink_density = float((ink > 0).mean())
    return boxes, {"edge_density": round(edge_density, 5), "ink_density": round(ink_density, 5)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract illustration crop candidates from page scans.")
    parser.add_argument("--volume", type=int, help="Process only one volume.")
    parser.add_argument("--force", action="store_true", help="Rebuild crop candidates and metadata.")
    parser.add_argument("--min-area", type=float, default=0.0045, help="Minimum connected-ink fraction.")
    parser.add_argument("--min-crop-area", type=float, default=0.02, help="Minimum crop area as a fraction of page area.")
    parser.add_argument("--min-crop-height", type=float, default=0.055, help="Minimum crop height as a fraction of page height.")
    parser.add_argument("--max-aspect", type=float, default=4.5, help="Maximum crop width divided by height.")
    parser.add_argument("--all-pages", action="store_true", help="Ignore visual_review.jsonl and scan every rendered page.")
    args = parser.parse_args()

    pages = read_jsonl(PAGE_INDEX)
    page_reviews: dict[str, dict[str, Any]] = {}
    if PAGE_REVIEW.is_file() and not args.all_pages:
        page_reviews = {row["page_id"]: row for row in read_jsonl(PAGE_REVIEW)}
        pages = [row for row in pages if page_reviews.get(row["page_id"], {}).get("contains_illustration") is True]
    if args.volume is not None:
        pages = [row for row in pages if int(row["volume"]) == args.volume]
    if not pages:
        raise SystemExit(f"No page rows found in {PAGE_INDEX}")

    existing = {row["id"]: row for row in read_jsonl(OUTPUT_INDEX)}
    seen_page_ids = {row["page_id"] for row in pages}
    if args.force and args.volume is not None:
        existing = {key: row for key, row in existing.items() if int(row["volume"]) != args.volume}
    elif args.force:
        existing = {}
    elif args.volume is None:
        existing = {key: row for key, row in existing.items() if row.get("page_id") not in seen_page_ids}

    output_rows = dict(existing)
    page_count = 0
    crop_count = 0
    expected_crop_files: set[Path] = set()
    for page_row in pages:
        page_path = PROJECT_ROOT / page_row["page_image"]
        if not page_path.is_file():
            continue
        image = cv2.imread(str(page_path), cv2.IMREAD_COLOR)
        if image is None:
            continue

        regions, page_metrics = find_regions(image, args.min_area)
        height, width = image.shape[:2]
        sx, sy = width / DETECTOR_WIDTH, height / max(1, round(DETECTOR_WIDTH * height / width))
        expanded: list[tuple[int, int, int, int]] = []
        for x0, y0, x1, y1 in regions:
            pad_x = round(DETECTOR_WIDTH * 0.018)
            pad_y = round(DETECTOR_WIDTH * 0.018)
            left = max(0, round((x0 - pad_x) * sx))
            top = max(0, round((y0 - pad_y) * sy))
            right = min(width, round((x1 + pad_x) * sx))
            bottom = min(height, round((y1 + pad_y) * sy))
            if right - left < width * 0.065 or bottom - top < height * 0.035:
                continue
            crop_width, crop_height = right - left, bottom - top
            if (crop_width * crop_height) / (width * height) < args.min_crop_area:
                continue
            if crop_height / height < args.min_crop_height or crop_width / crop_height > args.max_aspect:
                continue
            expanded.append((left, top, right, bottom))

        for ordinal, (left, top, right, bottom) in enumerate(expanded, start=1):
            page_id = page_row["page_id"]
            crop_id = f"{page_id}_i{ordinal:02d}"
            crop_path = PROJECT_ROOT / "dataset" / "candidates" / f"v{int(page_row['volume']):02d}" / f"{crop_id}.png"
            crop_path.parent.mkdir(parents=True, exist_ok=True)
            expected_crop_files.add(crop_path.resolve())
            Image.fromarray(cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2RGB)).save(
                crop_path,
                format="PNG",
                compress_level=1,
            )

            crop_gray = cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2GRAY)
            sharpness = float(cv2.Laplacian(crop_gray, cv2.CV_64F).var())
            row = {
                "id": crop_id,
                "page_id": page_id,
                "volume": int(page_row["volume"]),
                "book_title": page_row["title"],
                "source_pdf": page_row["source_pdf"],
                "page_number": int(page_row["page_number"]),
                "bbox_px": [left, top, right, bottom],
                "bbox_normalized": [round(left / width, 5), round(top / height, 5), round(right / width, 5), round(bottom / height, 5)],
                "page_image": page_row["page_image"],
                "crop_image": str(crop_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "crop_width_px": right - left,
                "crop_height_px": bottom - top,
                "crop_area_fraction": round(((right - left) * (bottom - top)) / (width * height), 5),
                "scan_sharpness_laplacian": round(sharpness, 3),
                "page_metrics": page_metrics,
                "page_review": page_reviews.get(page_id),
                "status": "candidate_pending_visual_review",
                "detector": "opencv_connected_ink_regions_v1",
            }
            output_rows[crop_id] = row
            crop_count += 1

        page_count += 1
        if page_count % 100 == 0:
            write_rows(output_rows)
            print(f"Scanned {page_count} pages; found {crop_count} crop candidates", flush=True)

    if args.force or args.volume is not None:
        volume_dirs = (
            [PROJECT_ROOT / "dataset" / "candidates" / f"v{args.volume:02d}"]
            if args.volume is not None
            else [PROJECT_ROOT / "dataset" / "candidates" / f"v{int(row['volume']):02d}" for row in pages]
        )
        for volume_dir in set(volume_dirs):
            if not volume_dir.is_dir():
                continue
            for old_crop in volume_dir.glob("c09_v*_p*_i*.png"):
                if old_crop.resolve() not in expected_crop_files:
                    old_crop.unlink()

    write_rows(output_rows)
    print(f"Done: scanned {page_count} pages; wrote {crop_count} candidate crops.")
    return 0


def write_rows(rows: dict[str, dict[str, Any]]) -> None:
    OUTPUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_INDEX.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in sorted(rows.values(), key=lambda item: (int(item["volume"]), int(item["page_number"]), item["id"])):
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(OUTPUT_INDEX)


if __name__ == "__main__":
    raise SystemExit(main())
