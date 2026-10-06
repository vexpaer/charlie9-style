"""Create labeled visual review sheets from rendered pages or a review queue."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build paginated contact sheets for AI visual inspection.")
    parser.add_argument("--input", default="metadata/pages.jsonl", help="JSONL page index or review queue.")
    parser.add_argument("--output", default="reports/contact_sheets", help="Output folder, relative to project root.")
    parser.add_argument("--per-sheet", type=int, default=100)
    parser.add_argument("--columns", type=int, default=10)
    parser.add_argument("--thumb-width", type=int, default=120)
    parser.add_argument("--volume", type=int, default=None, help="Only include one volume.")
    parser.add_argument("--candidates", action="store_true", help="Use crop_image and label each crop ID.")
    parser.add_argument("--global", dest="global_sheet", action="store_true", help="Mix volumes into one numbered sheet sequence.")
    args = parser.parse_args()

    input_path = (PROJECT_ROOT / args.input).resolve()
    output_root = (PROJECT_ROOT / args.output).resolve()
    rows = load_rows(input_path)
    if args.volume is not None:
        rows = [row for row in rows if int(row["volume"]) == args.volume]
    rows.sort(key=lambda row: (int(row["volume"]), int(row["page_number"])))
    if not rows:
        raise SystemExit(f"No pages found in {input_path}")

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()

    grouped_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    if args.global_sheet:
        grouped_rows[0].extend(rows)
    else:
        for row in rows:
            grouped_rows[int(row["volume"])].append(row)

    sheet_index = []
    for volume, volume_rows in sorted(grouped_rows.items()):
        for offset in range(0, len(volume_rows), args.per_sheet):
            batch = volume_rows[offset:offset + args.per_sheet]
            thumbnails = []
            thumb_height = 190
            label_height = 24
            cell_height = thumb_height + label_height
            for row in batch:
                image_field = ("crop_image" if row.get("crop_image") else "reference_image") if args.candidates else "page_image"
                image_path = PROJECT_ROOT / row.get(image_field, row.get("image", ""))
                if not image_path.is_file():
                    continue
                try:
                    with Image.open(image_path) as source:
                        source = source.convert("RGB")
                        scale = min(args.thumb_width / source.width, thumb_height / source.height)
                        size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
                        thumbnail = source.resize(size, Image.Resampling.LANCZOS)
                except OSError as exc:
                    print(f"Skipped unreadable image {image_path}: {exc}")
                    continue
                thumbnails.append((row, thumbnail))

            if not thumbnails:
                continue

            rows_count = (len(thumbnails) + args.columns - 1) // args.columns
            cell_width = args.thumb_width + 12
            sheet = Image.new("RGB", (args.columns * cell_width, rows_count * cell_height), "#e7e7e7")
            draw = ImageDraw.Draw(sheet)
            for index, (row, thumbnail) in enumerate(thumbnails):
                column, row_number = index % args.columns, index // args.columns
                x = column * cell_width + 6
                y = row_number * cell_height
                sheet.paste(thumbnail, (x + (args.thumb_width - thumbnail.width) // 2, y))
                label = row["id"] if args.candidates else f"v{int(row['volume']):02d} p{int(row['page_number']):04d}"
                draw.text((x, y + thumb_height + 3), label, fill="#101010", font=font)

            first = batch[0]
            last = batch[-1]
            folder = output_root / ("all" if args.global_sheet else f"v{volume:02d}")
            folder.mkdir(parents=True, exist_ok=True)
            prefix = "candidates-" if args.candidates else ""
            if args.global_sheet:
                filename = f"{prefix}{offset // args.per_sheet + 1:03d}.jpg"
            else:
                filename = f"{prefix}p{int(first['page_number']):04d}-p{int(last['page_number']):04d}.jpg"
            output_path = folder / filename
            sheet.save(output_path, quality=90, optimize=True)
            sheet_index.append({
                "file": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "count": len(thumbnails),
                "volume": None if args.global_sheet else volume,
                "first_page_id": batch[0]["page_id"],
                "last_page_id": batch[-1]["page_id"],
            })
            print(f"Created {output_path.relative_to(PROJECT_ROOT)} ({len(thumbnails)} pages)", flush=True)

    index_path = output_root / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(sheet_index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Contact sheets: {len(sheet_index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
