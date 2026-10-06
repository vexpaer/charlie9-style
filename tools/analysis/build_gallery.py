"""Build a local HTML gallery with source traceability for every crop candidate."""

from __future__ import annotations

import html
import json
import argparse
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX = PROJECT_ROOT / "metadata" / "illustrations.jsonl"
def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local HTML gallery for crop candidates or curated references.")
    parser.add_argument("--input", default="metadata/illustrations.jsonl", help="JSONL metadata file relative to project root.")
    parser.add_argument("--output", default="reports/extraction-report.html", help="HTML output path relative to project root.")
    parser.add_argument("--title", default="《查理九世》插画候选图册")
    args = parser.parse_args()

    input_path = (PROJECT_ROOT / args.input).resolve()
    output_path = (PROJECT_ROOT / args.output).resolve()
    if not input_path.is_file():
        raise SystemExit(f"Missing crop index: {input_path}")
    rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda row: (int(row["volume"]), int(row["page_number"]), row["id"]))
    volume_counts = Counter(int(row["volume"]) for row in rows)
    status_counts = Counter(str(row.get("visual_review_status", row.get("status", "not_reviewed"))) for row in rows)
    cards = []
    for row in rows:
        image_field = "crop_image" if row.get("crop_image") else "reference_image"
        relative_image = "../" + row[image_field].replace("\\", "/")
        source_pdf = html.escape(str(row.get("source_pdf", "")))
        status = html.escape(str(row.get("visual_review_status", row.get("status", "not_reviewed"))))
        dedup = html.escape(str(row.get("dedup_status", "not_scored")))
        score = row.get("quality_score", "")
        tags = html.escape(", ".join(row.get("visual_tags", [])))
        cards.append(
            "<article class='card' data-volume='{volume}' data-status='{status}' data-dedup='{dedup}'>"
            "<a href='{image}' target='_blank' rel='noreferrer'><img loading='lazy' src='{image}' alt='{id}'></a>"
            "<div class='meta'><strong>{id}</strong><br>第{volume}册 · PDF第{page}页 · {w}×{h}px<br>"
            "质量 {score} · {dedup}<br><span>{source}</span><br>{tags}</div></article>".format(
                volume=int(row["volume"]),
                status=status,
                dedup=dedup,
                image=html.escape(relative_image, quote=True),
                id=html.escape(row["id"]),
                page=int(row["page_number"]),
                w=int(row.get("crop_width_px", 0)),
                h=int(row.get("crop_height_px", 0)),
                score=html.escape(str(score)),
                source=source_pdf,
                tags=tags,
            )
        )

    options = "".join(f"<option value='{volume}'>第{volume}册 ({count})</option>" for volume, count in sorted(volume_counts.items()))
    status_options = "".join(
        f"<option value='{html.escape(status, quote=True)}'>{html.escape(status)} ({count})</option>"
        for status, count in sorted(status_counts.items())
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f2f1ee;color:#171717}}header{{position:sticky;top:0;background:#fff;padding:16px 24px;box-shadow:0 2px 12px #0002;z-index:2}}h1{{font-size:20px;margin:0 0 8px}}select,input{{padding:7px 10px;margin-right:8px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(205px,1fr));gap:12px;padding:16px}}.card{{background:white;border:1px solid #ddd;border-radius:7px;overflow:hidden}}.card img{{display:block;width:100%;height:260px;object-fit:contain;background:#e7e7e7}}.meta{{padding:9px;overflow-wrap:anywhere;font-size:12px}}.meta span{{color:#555}}.hidden{{display:none}}
 </style><header><h1>{title}</h1><div>{total} 张图；裁切保留原扫描像素和来源信息。</div><p><select id="volume"><option value="all">全部卷</option>{options}</select><select id="status"><option value="all">全部复核状态</option>{status_options}</select><select id="dedup"><option value="all">全部去重状态</option><option value="unique_or_best_in_group">去重后保留</option><option value="near_duplicate_lower_quality">近重复</option></select><input id="search" placeholder="搜索页码或文件名"></p></header><main class="grid">{cards}</main>
<script>const cards=[...document.querySelectorAll('.card')];function update(){{const v=document.getElementById('volume').value,s=document.getElementById('status').value,d=document.getElementById('dedup').value,q=document.getElementById('search').value.toLowerCase();for(const c of cards){{const hitV=v==='all'||c.dataset.volume===v;const hitS=s==='all'||c.dataset.status===s;const hitD=d==='all'||c.dataset.dedup===d;const hitQ=!q||c.textContent.toLowerCase().includes(q);c.classList.toggle('hidden',!(hitV&&hitS&&hitD&&hitQ))}}}}for(const id of ['volume','status','dedup','search'])document.getElementById(id).addEventListener('input',update);</script></html>""".format(title=html.escape(args.title), total=len(rows), options=options, status_options=status_options, cards="\n".join(cards)),
        encoding="utf-8",
    )
    print(f"Created {output_path.relative_to(PROJECT_ROOT)} with {len(rows)} images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
