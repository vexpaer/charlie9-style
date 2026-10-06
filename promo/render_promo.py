"""Render the Charlie9 Style vertical promo from the repository's own assets."""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PROMO = Path(__file__).resolve().parent
OUT = PROMO / "charlie9-style_promo_vertical.mp4"
W, H, FPS, SECONDS = 720, 1280, 30, 20
FRAMES = FPS * SECONDS
PAGE_X, PAGE_Y, PAGE_W, PAGE_H = 58, 150, 604, 930
PAPER = (242, 237, 226)
INK = (24, 29, 28)
ACCENT = (166, 76, 48)
FONT_CJK = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_CJK_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_SERIF = Path(r"C:\Windows\Fonts\georgia.ttf")
FONT_SANS = Path(r"C:\Windows\Fonts\arial.ttf")

SLOW_REFS = [
    "references/representative/story_scene/c09_v26_p0035_i01.png",
    "references/representative/story_scene/c09_v19_p0025_i01.png",
    "references/representative/story_scene/c09_v12_p0034_i01.png",
    "references/representative/story_scene/c09_v21_p0071_i01.png",
]
FAST_REFS = [
    "references/representative/story_scene/c09_v23_p0010_i01.png",
    "references/representative/story_scene/c09_v23_p0020_i01.png",
    "references/representative/story_scene/c09_v14_p0052_i01.png",
    "references/representative/story_scene/c09_v10_p0056_i01.png",
    "references/representative/story_scene/c09_v19_p0051_i01.png",
    "references/representative/story_scene/c09_v21_p0018_i01.png",
    "references/representative/story_scene/c09_v18_p0126_i01.png",
    "references/representative/story_scene/c09_v17_p0033_i02.png",
]
HOOK_DURATION = 2.20
HOOK_WIPE_START, HOOK_WIPE_DURATION = 0.72, 0.82
INTRO_START = 2.30
PAGE_FADE = 0.10
SLOW_PAGE_SPAN = 0.89
FAST_DURATIONS = [0.33, 0.26, 0.20, 0.15, 0.12, 0.085, 0.065, 0.05]
INTRO_DURATION = SLOW_PAGE_SPAN * len(SLOW_REFS) + sum(FAST_DURATIONS)
INTRO_END = INTRO_START + INTRO_DURATION
DEMO_START, DEMO_END = 7.20, 13.30
DEMO_REVEAL = 0.18
DEMO_VISUAL_START = DEMO_START + DEMO_REVEAL
DEMO_DURATION = (DEMO_END - DEMO_VISUAL_START) / 3
STATS_START, CTA_START = DEMO_END, 16.25


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.contain(image.convert("RGB"), size, Image.Resampling.LANCZOS)


def rounded_paste(canvas: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int = 12) -> None:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=radius, fill=255)
    canvas.paste(image, xy, mask)


def make_background(light: bool, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    radius = np.sqrt(((xx - W * 0.50) / W) ** 2 + ((yy - H * 0.44) / H) ** 2)
    vignette = np.clip(radius / 0.72, 0, 1)[..., None]
    if light:
        center = np.array((246, 242, 232), dtype=np.float32)
        edge = np.array((222, 216, 200), dtype=np.float32)
    else:
        center = np.array((29, 34, 31), dtype=np.float32)
        edge = np.array((10, 14, 13), dtype=np.float32)
    base = center * (1 - vignette * 0.72) + edge * (vignette * 0.72)
    grain = rng.normal(0, 1.45 if light else 0.75, (H, W, 1)).astype(np.float32)
    pixels = np.clip(base + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(pixels, "RGB")


DARK_BG = make_background(False, 19)
LIGHT_BG = make_background(True, 29)
WHITE_BG = Image.new("RGB", (W, H), (250, 248, 241))


def make_page(relative: str) -> Image.Image:
    source = Image.open(ROOT / relative).convert("RGB")
    page_img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(page_img)
    draw.rectangle((0, 0, PAGE_W - 1, PAGE_H - 1), outline=(213, 206, 191), width=2)
    box = (PAGE_W - 28, PAGE_H - 28)
    if source.width / source.height > 0.9:
        center = (0.68, 0.62) if "c09_v23_p0010" in relative else (0.5, 0.5)
        art = ImageOps.fit(source, box, Image.Resampling.LANCZOS, centering=center)
    else:
        art = fit(source, box)
    ax, ay = (PAGE_W - art.width) // 2, (PAGE_H - art.height) // 2
    page_img.paste(art, (ax, ay))
    return page_img


def make_hook_scenes() -> tuple[Image.Image, Image.Image]:
    comparison = Image.open(ROOT / "examples/basketball-court-comparison.png").convert("RGB")
    split = comparison.height // 2
    crop_box = (0, 0, 576, split)
    photo = ImageOps.fit(comparison.crop(crop_box), (W, H), Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    illustration = ImageOps.fit(
        comparison.crop((0, split, 576, comparison.height)),
        (W, H), Image.Resampling.LANCZOS, centering=(0.5, 0.5),
    )

    # The two short lines reproduce the repository's real example prompt.
    pixels = np.zeros((350, W, 4), dtype=np.uint8)
    y = np.arange(350, dtype=np.float32)
    pixels[:, :, 3] = np.clip(205 * (1 - y / 350) ** 1.35, 0, 205).astype(np.uint8)[:, None]
    pixels[:, :, :3] = (12, 15, 14)
    gradient = Image.fromarray(pixels, "RGBA")
    copy = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    copy.alpha_composite(gradient, (0, 0))
    draw = ImageDraw.Draw(copy)
    prompt_font = font(FONT_CJK_BOLD, 34)
    draw.text((48, 92), "根据这张照片生成", font=prompt_font, fill=(250, 247, 237), stroke_width=1, stroke_fill=(12, 15, 14))
    draw.text((48, 145), "黑白插画，保留原构图和人物位置。", font=prompt_font, fill=(250, 247, 237), stroke_width=1, stroke_fill=(12, 15, 14))
    photo = Image.alpha_composite(photo.convert("RGBA"), copy).convert("RGB")
    illustration = Image.alpha_composite(illustration.convert("RGBA"), copy).convert("RGB")
    return photo, illustration


def intro_frame(t: float, pages: list[Image.Image]) -> Image.Image:
    base = DARK_BG.copy()
    draw = ImageDraw.Draw(base)
    draw.text((W // 2, 78), "从原作中，找到下一笔。", font=font(FONT_CJK_BOLD, 35), fill=(239, 233, 219), anchor="mm")

    old_index, new_index, turn_progress = 0, 0, None
    slow_span = SLOW_PAGE_SPAN
    if t < slow_span * len(SLOW_REFS):
        slot = min(int(t / slow_span), len(SLOW_REFS) - 1)
        old_index = slot
        if slot < len(SLOW_REFS) - 1 and t % slow_span >= slow_span - 0.26:
            new_index = slot + 1
            turn_progress = min(1.0, (t % slow_span - (slow_span - 0.26)) / 0.26)
        else:
            new_index = slot
    else:
        elapsed = t - slow_span * len(SLOW_REFS)
        rapid_pages = [len(SLOW_REFS) - 1] + list(range(len(SLOW_REFS), len(pages)))
        cursor = 0.0
        old_index, new_index = rapid_pages[0], rapid_pages[0]
        for i, duration in enumerate(FAST_DURATIONS):
            if elapsed < cursor + duration:
                p = (elapsed - cursor) / duration
                old_index, new_index = rapid_pages[i], rapid_pages[i + 1]
                turn_progress = min(1.0, max(0.0, p / 0.82))
                break
            cursor += duration
            old_index = new_index = rapid_pages[i + 1]
        else:
            old_index = new_index = rapid_pages[-1]

    old_page, new_page = pages[old_index], pages[new_index]
    # Offset cream leaves under the active sheet; the curled edge catches a warm highlight.
    for offset, color in ((8, (184, 174, 153)), (4, (211, 202, 184))):
        draw.rounded_rectangle((PAGE_X + offset, PAGE_Y + 4, PAGE_X + PAGE_W + offset, PAGE_Y + PAGE_H + 4), radius=2, fill=color)
    shadow = Image.new("RGBA", (PAGE_W + 70, PAGE_H + 70), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((35, 35, PAGE_W + 35, PAGE_H + 35), radius=2, fill=(0, 0, 0, 132))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.paste(shadow, (PAGE_X - 35, PAGE_Y - 18), shadow)
    base.paste(new_page, (PAGE_X, PAGE_Y))
    if turn_progress is not None and turn_progress < 1:
        eased = math.sin(turn_progress * math.pi / 2)
        width = max(2, round(PAGE_W * (1 - eased)))
        front = old_page.resize((width, PAGE_H), Image.Resampling.LANCZOS)
        # A little perspective taper and a moving fold line sell the physical page turn.
        taper = max(0, round((1 - turn_progress) * 10))
        base.paste(front, (PAGE_X, PAGE_Y + taper // 2))
        fold_x = PAGE_X + width
        if width > 4:
            ImageDraw.Draw(base).rectangle((fold_x - 3, PAGE_Y + 5, fold_x + 3, PAGE_Y + PAGE_H - 5), fill=(222, 213, 194))
            ImageDraw.Draw(base).line((fold_x - 1, PAGE_Y + 9, fold_x - 1, PAGE_Y + PAGE_H - 9), fill=(255, 250, 234), width=2)

    # The final leaves accelerate into a paper-white flash.
    flash = float(np.clip((t - (INTRO_DURATION - 0.45)) / 0.45, 0, 1))
    if flash:
        flash = flash * flash * (3 - 2 * flash)
        base = Image.blend(base, WHITE_BG, flash)
    return base


def make_demo(index: int) -> Image.Image:
    canvas = LIGHT_BG.copy()
    title_text = ["让人物一眼可读", "让场景讲出故事", "让悬念藏在画面里"][index]
    caption = ["动作先于说明。", "把视线带进故事深处。", "悬念，藏在尺度与遮挡之间。"][index]
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((56, 128, 61, 190), radius=2, fill=ACCENT)
    draw.text((80, 158), title_text, font=font(FONT_CJK_BOLD, 40), fill=INK, anchor="lm")

    if index == 0:
        image = Image.open(ROOT / "examples/characters.png").convert("RGB")
        image = fit(image, (W - 88, 440))
        draw.rounded_rectangle((36, 274, W - 36, 764), radius=12, fill=(231, 224, 209))
        rounded_paste(canvas, image, (44, 299 + (440 - image.height) // 2), 8)
    elif index == 1:
        image = Image.open(ROOT / "examples/lakeside.png").convert("RGB")
        image = ImageOps.fit(image, (476, 760), Image.Resampling.LANCZOS, centering=(0.5, 0.52))
        draw.rounded_rectangle((112, 268, 608, 1044), radius=10, fill=(229, 223, 210))
        rounded_paste(canvas, image, (122, 278), 5)
    else:
        image = Image.open(ROOT / "examples/creature-encounter.png").convert("RGB")
        image = ImageOps.fit(image, (476, 760), Image.Resampling.LANCZOS, centering=(0.5, 0.46))
        draw.rounded_rectangle((112, 268, 608, 1044), radius=10, fill=(35, 37, 35))
        rounded_paste(canvas, image, (122, 278), 5)

    draw = ImageDraw.Draw(canvas)
    draw.text((W // 2, 1135), caption, font=font(FONT_CJK_BOLD, 29), fill=INK, anchor="mm")
    return canvas


def make_stats(pages: list[Image.Image]) -> Image.Image:
    canvas = LIGHT_BG.copy()
    d = ImageDraw.Draw(canvas)
    d.text((56, 115), "把画面感，拆解成可复用的方法。", font=font(FONT_CJK_BOLD, 40), fill=INK)

    picks = [0, 2, 3, 5]
    x, y, tile_w, tile_h, gap = 56, 230, 144, 205, 8
    for i, page_i in enumerate(picks):
        tile = pages[page_i].crop((20, 66, PAGE_W - 20, PAGE_H - 55))
        tile = ImageOps.fit(tile, (tile_w, tile_h), Image.Resampling.LANCZOS, centering=(0.5, 0.48))
        rounded_paste(canvas, tile, (x + i * (tile_w + gap), y), 5)
    d = ImageDraw.Draw(canvas)
    d.line((56, 470, W - 56, 470), fill=(190, 181, 163), width=1)

    stats = [("27", "原作册数"), ("141", "参考插画"), ("10", "专题笔记")]
    card_w, card_y, card_h, card_gap = 192, 535, 252, 16
    for i, (value, label) in enumerate(stats):
        cx = 46 + i * (card_w + card_gap)
        d.rounded_rectangle((cx, card_y, cx + card_w, card_y + card_h), radius=10, fill=(235, 229, 217), outline=(207, 198, 179), width=1)
        d.text((cx + card_w // 2, card_y + 94), value, font=font(FONT_SERIF, 70), fill=INK, anchor="mm")
        d.line((cx + 42, card_y + 157, cx + card_w - 42, card_y + 157), fill=ACCENT, width=2)
        d.text((cx + card_w // 2, card_y + 206), label, font=font(FONT_CJK_BOLD, 22), fill=(78, 76, 67), anchor="mm")
    return canvas


def make_cta() -> Image.Image:
    canvas = DARK_BG.copy()
    d = ImageDraw.Draw(canvas)
    d.text((W // 2, 354), "Charlie9", font=font(FONT_SERIF, 74), fill=(243, 238, 224), anchor="mm")
    d.text((W // 2, 440), "STYLE", font=font(FONT_SERIF, 51), fill=(193, 111, 75), anchor="mm")
    d.text((W // 2, 548), "少年冒险插画的风格参考", font=font(FONT_CJK_BOLD, 29), fill=(239, 233, 219), anchor="mm")
    d.text((W // 2, 596), "与创作指南", font=font(FONT_CJK_BOLD, 29), fill=(239, 233, 219), anchor="mm")

    # A small fan of paper leaves carries the page-turn motif into the end card.
    for i, color in enumerate(((133, 125, 106), (173, 162, 138), (221, 212, 192))):
        x = 164 + i * 26
        d.rounded_rectangle((x, 710 - i * 8, W - x, 861 + i * 8), radius=4, fill=color)
    d.rounded_rectangle((190, 688, W - 190, 870), radius=4, fill=(239, 233, 219))
    d.text((W // 2, 754), "把故事感，变成", font=font(FONT_CJK_BOLD, 25), fill=(66, 66, 59), anchor="mm")
    d.text((W // 2, 802), "可复用的创作方法。", font=font(FONT_CJK_BOLD, 25), fill=(66, 66, 59), anchor="mm")

    d.rounded_rectangle((44, 1010, W - 44, 1110), radius=9, fill=(185, 91, 58))
    d.text((W // 2, 1060), "github.com/vexpaer/charlie9-style", font=font(FONT_SANS, 23), fill=(255, 249, 239), anchor="mm")
    return canvas


def ease(value: float) -> float:
    x = float(np.clip(value, 0, 1))
    return x * x * (3 - 2 * x)


def transition_wipe(old: Image.Image, new: Image.Image, progress: float) -> Image.Image:
    p = ease(progress)
    reveal = int(W * p)
    frame = old.copy()
    if reveal > 0:
        frame.paste(new.crop((W - reveal, 0, W, H)), (W - reveal, 0))
        edge_x = W - reveal
        if 2 < edge_x < W - 2:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.rectangle((edge_x - 8, 0, edge_x + 2, H), fill=(35, 29, 19, 22))
            ld.rectangle((edge_x - 2, 0, edge_x + 1, H), fill=(255, 250, 237, 120))
            frame = Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")
    return frame


def visual_frame(t: float, hook: tuple[Image.Image, Image.Image], pages: list[Image.Image], demos: list[Image.Image], stats: Image.Image, cta: Image.Image) -> Image.Image:
    if t < HOOK_DURATION:
        photo, illustration = hook
        if t < HOOK_WIPE_START:
            frame = photo
        elif t < HOOK_WIPE_START + HOOK_WIPE_DURATION:
            progress = (t - HOOK_WIPE_START) / HOOK_WIPE_DURATION
            frame = transition_wipe(photo, illustration, progress)
        elif t < HOOK_DURATION - 0.16:
            frame = illustration
        else:
            frame = illustration
        if t >= HOOK_DURATION - 0.16:
            frame = Image.blend(frame, WHITE_BG, ease((t - (HOOK_DURATION - 0.16)) / 0.16))
        return frame
    if t < INTRO_START:
        intro = intro_frame(0, pages)
        return Image.blend(WHITE_BG, intro, ease((t - HOOK_DURATION) / PAGE_FADE))
    if t < INTRO_END:
        return intro_frame(t - INTRO_START, pages)
    if t < DEMO_START:
        return WHITE_BG
    if t < DEMO_END:
        if t < DEMO_VISUAL_START:
            return Image.blend(WHITE_BG, demos[0], ease((t - DEMO_START) / DEMO_REVEAL))
        position = t - DEMO_VISUAL_START
        idx = min(2, int(position / DEMO_DURATION))
        local = position - idx * DEMO_DURATION
        if idx < 2 and local >= DEMO_DURATION - 0.24:
            return transition_wipe(demos[idx], demos[idx + 1], (local - (DEMO_DURATION - 0.24)) / 0.24)
        return demos[idx]
    if t < CTA_START:
        stats_t = t - STATS_START
        if stats_t < 0.20:
            return Image.blend(demos[-1], stats, ease(stats_t / 0.20))
        return stats
    cta_t = t - CTA_START
    if cta_t < 0.26:
        return Image.blend(stats, cta, ease(cta_t / 0.26))
    return cta


def synthesize_score(path: Path) -> None:
    sr = 48000
    n = sr * SECONDS
    t = np.arange(n, dtype=np.float32) / sr
    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)

    # Warm, original bell-and-pad score; no stock track or voice recording.
    pad = np.zeros(n, dtype=np.float32)
    for j, hz in enumerate((73.42, 110.0, 146.83, 220.0, 293.66)):
        phase = j * 0.71
        wobble = 1 + 0.004 * np.sin(2 * np.pi * (0.055 + 0.01 * j) * t + phase)
        tone = np.sin(2 * np.pi * hz * t * wobble + phase)
        tone += 0.22 * np.sin(2 * np.pi * hz * 2 * t * wobble + phase * 0.7)
        pad += tone.astype(np.float32) * (0.0042 / (1 + j * 0.35))
    fade_in = np.clip(t / 1.2, 0, 1)
    fade_out = np.clip((SECONDS - t) / 1.3, 0, 1)
    swell = 0.68 + 0.24 * np.sin(np.pi * np.clip(t / SECONDS, 0, 1))
    left += pad * fade_in * fade_out * swell
    right += np.roll(pad, 740) * fade_in * fade_out * swell

    notes = (293.66, 349.23, 440.0, 392.0, 523.25, 440.0, 349.23, 293.66, 392.0, 523.25, 587.33, 440.0)
    onset = 0.32
    rng = np.random.default_rng(20261006)
    while onset < 19.0:
        hz = notes[int(onset * 1.17) % len(notes)]
        length = min(int(sr * 1.30), n - int(onset * sr))
        start = int(onset * sr)
        local = np.arange(length, dtype=np.float32) / sr
        envelope = (1 - np.exp(-local * 42)) * np.exp(-local * 3.2)
        pluck = (np.sin(2 * np.pi * hz * local) + 0.30 * np.sin(2 * np.pi * hz * 2.01 * local + 0.2) + 0.12 * np.sin(2 * np.pi * hz * 3.98 * local)) * envelope * 0.052
        pan = 0.30 + 0.40 * (0.5 + 0.5 * math.sin(onset * 1.7))
        left[start:start + length] += pluck * math.sqrt(1 - pan)
        right[start:start + length] += pluck * math.sqrt(pan)
        onset += 0.88 if onset < 5 else (0.50 if onset < 7.2 else 0.78)

    # Soft paper swishes synchronize with the leaves, growing quicker toward white.
    turn_times = [HOOK_WIPE_START + 0.10]
    turn_times.extend(INTRO_START + i * SLOW_PAGE_SPAN + SLOW_PAGE_SPAN - 0.20 for i in range(len(SLOW_REFS) - 1))
    fast_cursor = SLOW_PAGE_SPAN * len(SLOW_REFS)
    for duration in FAST_DURATIONS:
        turn_times.append(INTRO_START + fast_cursor + duration * 0.24)
        fast_cursor += duration
    for i, start_s in enumerate(turn_times):
        length = int(sr * (0.32 if i < 3 else max(0.10, 0.30 - i * 0.014)))
        start = int(start_s * sr)
        if start + length >= n:
            continue
        noise = rng.normal(0, 1, length).astype(np.float32)
        noise = np.convolve(noise, np.ones(7, dtype=np.float32) / 7, mode="same")
        x = np.linspace(0, 1, length, dtype=np.float32)
        env = np.maximum(0.0, np.sin(np.pi * x)) ** 0.8
        strength = 0.018 if i < 3 else min(0.043, 0.017 + i * 0.002)
        swish = noise * env * strength
        left[start:start + length] += swish
        right[start:start + length] += np.roll(swish, 110)

    # A quiet harmonic bloom marks the white-out and resolves the final card.
    for start_s, hz, level in ((INTRO_END - 0.34, 659.25, 0.020), (INTRO_END - 0.20, 880.0, 0.018), (INTRO_END - 0.08, 1174.66, 0.014), (CTA_START - 0.70, 523.25, 0.014)):
        start = int(start_s * sr)
        length = min(int(sr * 1.05), n - start)
        local = np.arange(length, dtype=np.float32) / sr
        env = np.sin(np.pi * np.clip(local / 1.05, 0, 1)) ** 1.2
        tone = (np.sin(2 * np.pi * hz * local) + 0.22 * np.sin(2 * np.pi * hz * 2 * local)) * env * level
        left[start:start + length] += tone
        right[start:start + length] += np.roll(tone, 360)

    # Gentle short stereo reflections add a little room around the plucks.
    left[3400:] += right[:-3400] * 0.085
    right[4600:] += left[:-4600] * 0.075
    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), 1e-6)
    gain = 0.78 / peak
    stereo = np.stack((left * gain, right * gain), axis=1)
    pcm = np.clip(stereo * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(pcm.tobytes())


def render(output: Path) -> None:
    missing = [relative for relative in SLOW_REFS + FAST_REFS if not (ROOT / relative).is_file()]
    missing += [name for name in ("examples/basketball-court-comparison.png", "examples/characters.png", "examples/lakeside.png", "examples/creature-encounter.png") if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing project assets: " + ", ".join(missing))
    output.parent.mkdir(parents=True, exist_ok=True)

    pages = [make_page(relative) for relative in SLOW_REFS + FAST_REFS]
    hook = make_hook_scenes()
    demos = [make_demo(i) for i in range(3)]
    stats = make_stats(pages)
    cta = make_cta()

    with tempfile.TemporaryDirectory(prefix="charlie9-style-promo-") as temp:
        audio = Path(temp) / "original_score.wav"
        synthesize_score(audio)
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "pipe:0",
            "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-frames:v", str(FRAMES), "-t", str(SECONDS),
            "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        poster_path = output.with_name("charlie9-style_poster.jpg")
        assert process.stdin is not None
        try:
            for frame_index in range(FRAMES):
                timestamp = frame_index / FPS
                frame = visual_frame(timestamp, hook, pages, demos, stats, cta)
                if frame_index == 0:
                    poster = frame.resize((1080, 1920), Image.Resampling.LANCZOS)
                    poster.save(poster_path, quality=94, subsampling=0)
                process.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
                if frame_index % 120 == 0:
                    print(f"Rendering {timestamp:05.2f}s / {SECONDS}s", flush=True)
        except BrokenPipeError:
            process.stdin.close()
            raise RuntimeError("ffmpeg stopped before all frames were written")
        finally:
            process.stdin.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)
    print(f"Saved {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT, help=f"Output MP4 path (default: {OUT})")
    args = parser.parse_args()
    render(args.output.resolve())


if __name__ == "__main__":
    main()
