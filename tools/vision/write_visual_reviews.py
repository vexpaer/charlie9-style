"""Write page-level visual decisions from the reviewed contact-sheet seed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGES_INDEX = PROJECT_ROOT / "metadata" / "pages.jsonl"
SEED_PATH = PROJECT_ROOT / "metadata" / "visual_review_seed.json"
OUTPUT_PATH = PROJECT_ROOT / "metadata" / "visual_review.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Record visual contact-sheet review outcomes for rendered pages.")
    parser.add_argument("--volume", type=int, action="append", help="Limit write to one or more reviewed volumes.")
    args = parser.parse_args()
    page_rows = read_jsonl(PAGES_INDEX)
    seeds: dict[str, dict[str, list[int]]] = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    volumes = {int(value) for value in args.volume} if args.volume else {int(value) for value in seeds}
    existing = {row["page_id"]: row for row in read_jsonl(OUTPUT_PATH)}
    touched = {row["page_id"] for row in page_rows if int(row["volume"]) in volumes}
    records = {key: row for key, row in existing.items() if key not in touched}

    for page in page_rows:
        volume = int(page["volume"])
        if volume not in volumes or str(volume) not in seeds:
            continue
        page_number = int(page["page_number"])
        category = next(
            (name for name, numbers in seeds[str(volume)].items() if page_number in numbers),
            None,
        )
        records[page["page_id"]] = {
            "page_id": page["page_id"],
            "volume": volume,
            "page_number": page_number,
            "source_pdf": page["source_pdf"],
            "page_image": page["page_image"],
            "contains_illustration": category is not None,
            "visual_category": category or "text_or_nonillustrated_page",
            "visual_tags": [category] if category else [],
            "review_method": "built_in_codex_vision_contact_sheet_pass",
            "review_status": "page_reviewed",
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in sorted(records.values(), key=lambda item: (int(item["volume"]), int(item["page_number"]))):
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(OUTPUT_PATH)
    positives = sum(bool(row.get("contains_illustration")) for row in records.values())
    print(f"Wrote {len(records)} page reviews ({positives} pages contain visible art).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
