# Charlie9 Style promo

Vertical 20-second introduction to the `charlie9-style` Codex Skill. It opens with the repository's photo-to-illustration example, reveals the original illustration references through increasingly fast page turns and a warm-white flash, then shows three examples, corpus facts, and the repository end card. The score is composed in the render script; there is no voice-over or stock music.

## Render

From this directory, run:

```powershell
python .\render_promo.py
```

Requires Pillow, NumPy, and FFmpeg. The MP4 is written here as `charlie9-style_promo_vertical.mp4` (1080 × 1920, 30 fps, H.264/AAC); the opening frame is also exported as `charlie9-style_poster.jpg`.

## Timeline

- 0:00–0:02.2: match-cut the basketball-court photo to the repository's black-and-white illustration, with the real example prompt in large type.
- 0:02.3–0:07.125: four slow original-illustration pages accelerate into a warm-white flash.
- 0:07.2–0:13.3: character, environment, and suspense examples.
- 0:13.3–0:16.25: reference set and analysis counts.
- 0:16.25–0:20: skill title and GitHub repository link.

The opening photo transformation is an existing example; the Skill supplies style guidance and references, while image creation is done by an image-generation tool. The scanned reference images and example images remain subject to their rights holders' terms as described in [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
