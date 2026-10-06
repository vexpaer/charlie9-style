"""Compute crop quality scores and conservative perceptual near-duplicates."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX = PROJECT_ROOT / "metadata" / "illustrations.jsonl"
MAX_HAMMING_DISTANCE = 4


def load_rows() -> list[dict[str, Any]]:
    if not INDEX.exists():
        return []
    return [json.loads(line) for line in INDEX.read_text(encoding="utf-8").splitlines() if line.strip()]


def perceptual_hash(image: np.ndarray) -> int:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    frequencies = cv2.dct(small)[:8, :8]
    values = frequencies.flatten()[1:]
    median = float(np.median(values))
    bits = 0
    for value in values:
        bits = (bits << 1) | int(value > median)
    return bits


def hamming(left: int, right: int) -> int:
    return (left ^ right).bit_count()


class BKNode:
    def __init__(self, value: int, row_index: int):
        self.value = value
        self.row_index = row_index
        self.children: dict[int, BKNode] = {}


class BKTree:
    def __init__(self) -> None:
        self.root: BKNode | None = None

    def add(self, value: int, row_index: int) -> None:
        if self.root is None:
            self.root = BKNode(value, row_index)
            return
        node = self.root
        while True:
            distance = hamming(value, node.value)
            child = node.children.get(distance)
            if child is None:
                node.children[distance] = BKNode(value, row_index)
                return
            node = child

    def nearest(self, value: int, limit: int) -> tuple[int, int] | None:
        if self.root is None:
            return None
        best: tuple[int, int] | None = None
        pending = [self.root]
        while pending:
            node = pending.pop()
            distance = hamming(value, node.value)
            if distance <= limit and (best is None or distance < best[0]):
                best = (distance, node.row_index)
            low, high = distance - limit, distance + limit
            pending.extend(child for edge, child in node.children.items() if low <= edge <= high)
        return best


def quality_score(row: dict[str, Any], image: np.ndarray) -> tuple[float, dict[str, float]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    p05, p95 = np.percentile(gray, [5, 95])
    contrast = float(p95 - p05)
    size_score = min(1.0, min(width, height) / 700.0)
    sharp_score = min(1.0, math.log1p(max(sharpness, 0.0)) / math.log1p(1200.0))
    contrast_score = min(1.0, contrast / 170.0)
    area_score = min(1.0, float(row.get("crop_area_fraction", 0.0)) / 0.30)
    score = 0.30 * size_score + 0.30 * sharp_score + 0.20 * contrast_score + 0.20 * area_score
    return round(score, 5), {
        "size": round(size_score, 5),
        "sharpness": round(sharp_score, 5),
        "contrast": round(contrast_score, 5),
        "illustration_area": round(area_score, 5),
    }


def main() -> int:
    rows = load_rows()
    prepared: list[tuple[int, dict[str, Any], int]] = []
    missing = 0
    for row in rows:
        path = PROJECT_ROOT / row.get("crop_image", "")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR) if path.is_file() else None
        if image is None:
            row["dedup_status"] = "missing_or_unreadable"
            missing += 1
            continue
        row["quality_score"] , row["quality_components"] = quality_score(row, image)
        value = perceptual_hash(image)
        row["perceptual_hash"] = f"{value:016x}"
        prepared.append((value, row, len(prepared)))

    prepared.sort(key=lambda item: (-float(item[1]["quality_score"]), item[1]["id"]))
    tree = BKTree()
    representative_rows: list[dict[str, Any]] = []
    duplicate_count = 0
    for value, row, _ in prepared:
        match = tree.nearest(value, MAX_HAMMING_DISTANCE)
        if match is None:
            group = f"ph_{row['perceptual_hash']}"
            row["duplicate_group"] = group
            row["duplicate_of"] = None
            row["duplicate_distance"] = None
            row["dedup_status"] = "unique_or_best_in_group"
            tree.add(value, len(representative_rows))
            representative_rows.append(row)
        else:
            distance, representative_index = match
            representative = representative_rows[representative_index]
            row["duplicate_group"] = representative["duplicate_group"]
            row["duplicate_of"] = representative["id"]
            row["duplicate_distance"] = distance
            row["dedup_status"] = "near_duplicate_lower_quality"
            duplicate_count += 1

    ordered = sorted(rows, key=lambda row: (int(row["volume"]), int(row["page_number"]), row["id"]))
    temporary = INDEX.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in ordered:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(INDEX)
    print(f"Scored {len(prepared)} crops; {duplicate_count} near-duplicates; {missing} unreadable crops.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
