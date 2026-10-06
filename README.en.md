<div align="center">

# Charlie9 Style

**A reusable visual reference for expressive youth-adventure illustration.**

A Codex Skill and traceable reference collection built from 27 scanned Charlie 9 volumes.<br>
Monochrome storytelling · Character design · Environments · Photo-to-illustration

[简体中文](README.md) · **English**

[Quick start](#quick-start) · [Examples](#examples) · [Reference gallery](reports/representative-gallery.html) · [Skill guide](SKILL.md)

</div>

## Examples

<p align="center">
  <a href="reports/style-tests/readme-gallery.jpg"><img src="reports/style-tests/readme-gallery.jpg" height="560" alt="Two staggered rows: characters and a creature encounter above; a lakeside scene and a basketball court photo-to-illustration comparison below"></a>
</p>

<p align="center"><sub>Top: characters · creature encounter / Bottom: lakeside scene · photo-to-illustration</sub></p>

All four examples are shown in full, arranged in two rows using their original proportions. Display height is set to 560 px, with width following the aspect ratio. Click for the larger image.

[Characters](reports/style-tests/batch-02/06-07-montage.png) · [Creature encounter](reports/style-tests/03-creature-encounter.png) · [Lakeside scene](reports/style-tests/batch-02/03-lakeside-glow.png) · [Basketball court comparison](reports/style-tests/basketball-court-comparison.png)

## What you can do

- **Create new illustrations:** turn recurring visual traits into practical direction for youth adventure, mystery scenes, character vignettes, and environments.
- **Study the style visually:** browse 141 traceable reference crops alongside 10 focused analyses of linework, shading, composition, and more.
- **Illustrate a photograph:** retain its perspective and subject placement while expressing the scene through contours, hatching, and black-and-white values.
- **Trace each reference:** connect crops to their source volume, PDF page, and crop coordinates.

The Skill supplies instructions and reference images. An image generation tool performs the drawing; this project includes no trained weights or standalone generation service.

## Quick start

### Use it in this project

Open the workspace containing this project in Codex, point to [SKILL.md](SKILL.md), and describe your scene:

```text
Use charlie9-style/SKILL.md to illustrate three young explorers finding a faint glow
on a misty lake. Draw in black and white, with readable gestures and clear
foreground, middle-ground, and background layers.
```

For a photo-based illustration, attach the photo and describe what to preserve:

```text
Use charlie9-style to turn this photo into a monochrome illustration.
Preserve the court perspective, buildings, and people. Use clear contours
and fine hatching to describe the environment.
```

Creating an image requires image generation capabilities. You can also read the Skill to develop art direction and prompts.

### Reuse the Skill

Everyday illustration needs these three parts in the same skill folder:

```text
charlie9-style/
├── SKILL.md
├── analysis/
└── references/representative/
```

Preserve the relative directory structure so its images and supporting notes remain accessible. Source PDFs, full-page renders, and candidate crops are unnecessary for everyday illustration.

## Style guide

| Direction | Focus | Notes |
| --- | --- | --- |
| Characters | Readable expressions, gestures, distinct silhouettes | [Character design](analysis/character-design.md) |
| Lines and values | Varied contours, selective hatching, strong black-and-white shapes | [Linework](analysis/linework.md) · [Shading](analysis/shading.md) |
| Settings | Depth layers, perspective, natural and architectural detail | [Composition](analysis/composition.md) · [Perspective](analysis/perspective.md) · [Environments](analysis/environment.md) |
| Adventure and mystery | Scale contrasts, concealment, silhouettes, unusual forms | [Creature design](analysis/creature-design.md) · [Suspense](analysis/horror-language.md) |
| Color | Treatments selected from relevant references | [Color](analysis/color.md) |

Start with [core traits and evidence limits](analysis/style-core.md), then read the notes relevant to your image.

## Collection and method

| Item | Count |
| --- | ---: |
| Source scans | 27 volumes / 5,667 pages |
| Illustrated pages | 2,424 |
| Candidate crops | 3,660 |
| Best candidates after deduplication | 2,348 |
| Visually reviewed candidates | 406 |
| Selected references | 141: 108 scenes / 26 character vignettes / 7 front-matter images |

Workflow: **300-DPI rendering → contact-sheet visual review → candidate cropping → ranking and deduplication → stratified review → references and style notes**.

All 5,667 pages were reviewed with Codex's built-in image understanding. No local vision model was used. Selected references are unchanged copies of candidate crops; generated examples are stored separately.

- [Method and limitations](reports/style-report.md)
- [Selected references](reports/representative-gallery.html)
- [Page index](metadata/pages.jsonl) · [Crop index](metadata/illustrations.jsonl) · [Selected-reference manifest](metadata/representative_references.jsonl)

Download the HTML galleries and open them in a browser; GitHub file pages show their source code.

The public repository includes the Skill, style notes, selected references, provenance indexes, and generated examples. Source PDFs, full-page renders, candidate crops, and intermediate contact sheets remain local and are not distributed with the repository.

## Project layout

```text
charlie9-style/
├── SKILL.md                  # Reusable direction and visual references
├── analysis/                 # 10 focused style notes
├── references/representative/ # Selected, unchanged crops
├── reports/                  # Reports, galleries, generated examples
├── metadata/                 # Provenance, coordinates, review records
├── tools/                    # Rendering, cropping, deduplication, galleries
├── config/project.json       # Source location and rendering settings
└── dataset/                  # Full-page renders and candidate crops
```

### Rebuild page renders

Requires Python and source PDFs you have permission to use. Set `source_dir` in [config/project.json](config/project.json); it defaults to a sibling folder named `查理九世`.

Run from this directory with PowerShell 7:

```powershell
python -m pip install -r requirements.txt
python tools/extract/render_pages.py
```

Existing pages are skipped. Use `--limit 50` to limit the page count, or `--force` to render existing pages again. These commands rebuild page renders only; see the report for visual review and reference selection.

Rebuild the README gallery:

```powershell
python tools/analysis/build_readme_gallery.py
```

## Contributing

Reproducible bug reports, provenance corrections, evidence-based style notes, and tool improvements are welcome. Include file paths, source volume, and PDF page for reference issues; include commands and error output for tool issues. Discuss substantial structural changes first.

Preserve provenance for new references. Describe the references and generation method for new examples. Keep both language editions in sync when updating documentation.

## Sources and licensing

This project studies visible illustration traits in scanned Charlie 9 samples. It does not establish illustrator attribution or a uniform style across every volume, and is not an official project.

Code and original documentation are released under the [MIT license](LICENSE). Reference scans, photographs, and generated examples are excluded from this software license. Scans and reference crops belong to their respective rights holders. See [third-party notices](THIRD_PARTY_NOTICES.md) for details.
