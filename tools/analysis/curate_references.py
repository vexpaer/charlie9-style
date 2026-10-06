"""Apply the recorded contact-sheet review and copy exact representative crops."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUEUE = PROJECT_ROOT / "metadata" / "crop_review_queue.jsonl"
DECISIONS = PROJECT_ROOT / "metadata" / "curation_decisions.json"
INDEX = PROJECT_ROOT / "metadata" / "illustrations.jsonl"
REVIEW_OUTPUT = PROJECT_ROOT / "metadata" / "crop_visual_review.jsonl"
MANIFEST_OUTPUT = PROJECT_ROOT / "metadata" / "representative_references.jsonl"
REFERENCE_ROOT = PROJECT_ROOT / "references" / "representative"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    if not QUEUE.is_file() or not DECISIONS.is_file() or not INDEX.is_file():
        raise SystemExit("Missing crop queue, curation decisions, or illustration index.")

    queue = read_jsonl(QUEUE)
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    accepted = set(decisions.get("accepted_ids", []))
    explicit_rejections = decisions.get("rejected_ids", {})
    queue_by_id = {row["id"]: row for row in queue}
    unknown = sorted(accepted - set(queue_by_id))
    if unknown:
        raise SystemExit(f"Accepted IDs are missing from review queue: {unknown[:5]}")

    review_rows: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    status_by_id: dict[str, tuple[str, str]] = {}
    for row in queue:
        crop_id = row["id"]
        category = str(row["queue_category"])
        if crop_id in accepted:
            review_status = "accepted_reference"
            note = "Contact-sheet review: clear illustration crop selected for the representative set."
            destination = REFERENCE_ROOT / category / f"{crop_id}.png"
            source = PROJECT_ROOT / row["crop_image"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            manifest.append({
                "id": crop_id,
                "page_id": row.get("page_id", ""),
                "book_title": row.get("book_title", ""),
                "volume": int(row["volume"]),
                "page_number": int(row["page_number"]),
                "source_pdf": row.get("source_pdf", ""),
                "bbox_px": row.get("bbox_px", []),
                "bbox_normalized": row.get("bbox_normalized", []),
                "source_crop": row["crop_image"],
                "reference_image": str(destination.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "visual_category": category,
                "quality_score": row.get("quality_score"),
                "duplicate_group": row.get("duplicate_group"),
                "visual_review_status": "accepted_reference",
                "review_method": "built_in_codex_vision_contact_sheet_pass",
            })
        elif crop_id in explicit_rejections:
            review_status = "rejected_detector_artifact"
            note = str(explicit_rejections[crop_id])
        else:
            review_status = "reviewed_not_selected"
            note = "Viewed in the balanced contact-sheet queue; excluded to keep the set diverse and concise."

        status_by_id[crop_id] = (review_status, note)
        review_rows.append({
            "id": crop_id,
            "volume": int(row["volume"]),
            "page_number": int(row["page_number"]),
            "source_pdf": row.get("source_pdf", ""),
            "crop_image": row["crop_image"],
            "visual_category": category,
            "quality_score": row.get("quality_score"),
            "review_status": review_status,
            "review_note": note,
            "review_method": "built_in_codex_vision_contact_sheet_pass",
        })

    index_rows = read_jsonl(INDEX)
    for row in index_rows:
        if row["id"] in status_by_id:
            review_status, note = status_by_id[row["id"]]
            row["visual_review_status"] = review_status
            row["visual_review_note"] = note
            if review_status == "accepted_reference":
                row["status"] = "accepted_reference"
            elif review_status == "rejected_detector_artifact":
                row["status"] = "rejected_visual_review"
            else:
                row["status"] = "reviewed_not_selected"

    write_jsonl(INDEX, index_rows)
    write_jsonl(REVIEW_OUTPUT, review_rows)
    write_jsonl(MANIFEST_OUTPUT, sorted(manifest, key=lambda row: (row["volume"], row["visual_category"], row["page_number"])))
    print(f"Reviewed {len(review_rows)} crops; accepted {len(manifest)} exact crop copies as references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
