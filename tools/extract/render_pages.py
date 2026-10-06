"""Render source PDFs to traceable, lossless page images."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"
INDEX_PATH = PROJECT_ROOT / "metadata" / "pages.jsonl"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def book_info(path: Path) -> tuple[int, str]:
    match = re.match(r"\s*(\d+)\s*[•·.、_-]\s*(.*)$", path.stem)
    if match:
        return int(match.group(1)), match.group(2).strip()
    match = re.match(r"\s*(\d+)\s+(.*)$", path.stem)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return 0, path.stem.strip()


def read_index() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not INDEX_PATH.exists():
        return rows
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            rows[row["page_id"]] = row
        except (json.JSONDecodeError, KeyError):
            continue
    return rows


def write_index(rows: dict[str, dict[str, Any]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = INDEX_PATH.with_suffix(".jsonl.tmp")
    ordered = sorted(rows.values(), key=lambda row: (row["volume"], row["page_number"]))
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in ordered:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(INDEX_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render all source PDF pages at native scan scale.")
    parser.add_argument("--dpi", type=int, default=None, help="Render DPI; defaults to config/project.json.")
    parser.add_argument("--limit", type=int, default=None, help="Render only the first N pages for a pilot run.")
    parser.add_argument("--force", action="store_true", help="Replace existing rendered pages.")
    args = parser.parse_args()

    config = load_config()
    source_dir = (PROJECT_ROOT / config["source_dir"]).resolve()
    dpi = args.dpi or int(config.get("render_dpi", 300))
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {source_dir}")

    pdfs = sorted(source_dir.glob("*.pdf"), key=lambda path: (*book_info(path), path.name.casefold()))
    if not pdfs:
        raise SystemExit(f"No PDF files found in {source_dir}")

    rows = read_index()
    count = 0
    errors: list[dict[str, Any]] = []
    for pdf in pdfs:
        volume, title = book_info(pdf)
        relative_pdf = Path("..") / pdf.parent.name / pdf.name
        output_dir = PROJECT_ROOT / "dataset" / "pages" / f"v{volume:02d}"
        output_dir.mkdir(parents=True, exist_ok=True)
        document = fitz.open(pdf)
        try:
            for page_number, page in enumerate(document, start=1):
                if args.limit is not None and count >= args.limit:
                    break
                page_id = f"c09_v{volume:02d}_p{page_number:04d}"
                output_path = output_dir / f"{page_id}.png"
                if args.force or not output_path.exists():
                    temporary_path = output_path.with_name(output_path.stem + ".partial.png")
                    try:
                        pixmap = page.get_pixmap(
                            dpi=dpi,
                            colorspace=fitz.csRGB,
                            alpha=False,
                        )
                        pixmap.save(str(temporary_path))
                        temporary_path.replace(output_path)
                    except Exception as exc:
                        temporary_path.unlink(missing_ok=True)
                        errors.append({
                            "page_id": page_id,
                            "source_pdf": str(relative_pdf),
                            "page_number": page_number,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        continue

                rows[page_id] = {
                    "page_id": page_id,
                    "volume": volume,
                    "title": title,
                    "source_pdf": str(relative_pdf),
                    "page_number": page_number,
                    "page_width_pt": round(page.rect.width, 3),
                    "page_height_pt": round(page.rect.height, 3),
                    "render_dpi": dpi,
                    "render_width_px": int(round(page.rect.width * dpi / 72)),
                    "render_height_px": int(round(page.rect.height * dpi / 72)),
                    "page_image": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                }
                count += 1
                if count % 100 == 0:
                    write_index(rows)
                    print(f"Rendered/indexed {count} pages", flush=True)
            write_index(rows)
        finally:
            document.close()
        if args.limit is not None and count >= args.limit:
            break

    if errors:
        error_path = PROJECT_ROOT / "metadata" / "render_errors.jsonl"
        error_path.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in errors),
            encoding="utf-8",
        )
    print(f"Done: {count} pages indexed at {dpi} DPI; source PDFs were not modified.")
    if errors:
        print(f"Pages with render errors: {len(errors)}; see metadata/render_errors.jsonl.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
