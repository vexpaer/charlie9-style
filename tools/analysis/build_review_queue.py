"""Select a volume-balanced visual-review queue from deduplicated crop candidates."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX = PROJECT_ROOT / "metadata" / "illustrations.jsonl"


def read_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def best_per_page(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[tuple[int, int, str], dict[str, Any]] = {}
    for row in rows:
        key = (int(row["volume"]), int(row["page_number"]), str(row.get("visual_category", "")))
        current = chosen.get(key)
        if current is None or float(row.get("quality_score", 0.0)) > float(current.get("quality_score", 0.0)):
            chosen[key] = row
    return list(chosen.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a balanced crop review queue from deduplicated candidates.")
    parser.add_argument("--scene-per-volume", type=int, default=10)
    parser.add_argument("--vignette-per-volume", type=int, default=5)
    parser.add_argument("--front-matter-per-volume", type=int, default=1)
    parser.add_argument("--output", default="metadata/crop_review_queue.jsonl")
    args = parser.parse_args()

    if not INDEX.is_file():
        raise SystemExit(f"Missing crop index: {INDEX}")
    rows = read_rows(INDEX)
    eligible = [
        row for row in rows
        if row.get("dedup_status") == "unique_or_best_in_group"
        and (row.get("page_review") or {}).get("visual_category") in {"story_scene", "character_vignette", "front_matter"}
    ]
    eligible = best_per_page(eligible)
    by_volume_category: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        category = str((row.get("page_review") or {}).get("visual_category", ""))
        by_volume_category[(int(row["volume"]), category)].append(row)

    quotas = {
        "story_scene": args.scene_per_volume,
        "character_vignette": args.vignette_per_volume,
        "front_matter": args.front_matter_per_volume,
    }
    queue: list[dict[str, Any]] = []
    for volume in sorted({int(row["volume"]) for row in eligible}):
        for category, quota in quotas.items():
            candidates = sorted(
                by_volume_category.get((volume, category), []),
                key=lambda row: (-float(row.get("quality_score", 0.0)), int(row["page_number"]), row["id"]),
            )
            for rank, original in enumerate(candidates[:max(0, quota)], start=1):
                row = dict(original)
                row["queue_category"] = category
                row["queue_rank_in_category"] = rank
                row["visual_review_status"] = "pending"
                queue.append(row)

    queue.sort(key=lambda row: (int(row["volume"]), row["queue_category"], int(row["page_number"]), row["id"]))
    output = (PROJECT_ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in queue), encoding="utf-8")
    print(f"Wrote {len(queue)} balanced review crops to {output.relative_to(PROJECT_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
