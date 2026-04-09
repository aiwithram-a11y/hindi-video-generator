#!/usr/bin/env python3
"""
Hindi Video Generator V13 - Chrome Text Rendering
================================================
Uses Chrome/Puppeteer for text rendering - browsers have excellent 
Devanagari support via HarfBuzz for proper matra shaping.

This fixes the choti e matra and other matra issues that occur
with Pillow's lack of proper complex text layout support.

Usage:
    python3 generate_video_v13.py --article anjaan_satark_clean.md --output-dir output_v13
    python3 generate_video_v13.py --article article.md --output-dir output_v13 --bg-image /path/to/bg.jpg
"""

import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Optional
from PIL import Image

# ── Config ─────────────────────────────────────────────────────────────────────
VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
WATERMARK = "ramkrishan.com"
DEFAULT_BG_IMAGE = "/Users/ramdudeja/Desktop/Hindi-video-generator/image_rk_url.jpg"
TTS_VOICE = "Tara"
TTS_RATE = 158
CRF = 20

# Python renderer - no Node/Chrome needed
HINDI_FONT_PATHS = [
    "/Users/ramdudeja/Desktop/Hindi-video-generator/fonts/NotoSansDevanagari-Regular.ttf",
    "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    "/System/Library/Fonts/Kohinoor.ttc",
    "/Library/Fonts/NotoSansDevanagari-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]

# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Hindi Video Generator V13 - Chrome Text")
    p.add_argument("--article", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--bg-image", default=None, help="Background image (local path, URL, or 'ask' to prompt)")
    p.add_argument("--no-sarvam", action="store_true", help="Use macOS say instead of Sarvam")
    p.add_argument("--crf", type=int, default=20, help="CRF value")
    p.add_argument("--short", action="store_true", help="Short version")
    return p.parse_args()

ARGS = parse_args()

SCRIPT_DIR = Path(__file__).parent
ARTICLE_FILE = ARGS.article if ARGS.article else SCRIPT_DIR / "anjaan_satark_clean.md"
OUTPUT_DIR = Path(ARGS.output_dir) if ARGS.output_dir else SCRIPT_DIR / "output_v13"
CLIPS_DIR = OUTPUT_DIR / "clips"
AUDIO_DIR = OUTPUT_DIR / "audio"
TEXT_IMG_DIR = OUTPUT_DIR / "text_images"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

CRF = ARGS.crf
MAX_SENTENCES_SHORT = 2

# Sarvam TTS config
SARVAM_API_KEY = "sk_3rguk1va_YWUseNZY9XeLLRzSuOTzwyAa"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech/stream"

def ensure_dirs():
    for d in [OUTPUT_DIR, CLIPS_DIR, AUDIO_DIR, TEXT_IMG_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# ── Text Renderer: Playwright (primary) + Pillow (fallback) ───────────────────

# Fonts with broad Unicode coverage (Latin + Devanagari) used by Pillow fallback.
# Arial Unicode MS is prioritised because it covers both scripts on every Mac.
BROAD_FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",   # Latin + Devanagari
    "/System/Library/Fonts/Kohinoor.ttc",                      # Devanagari (good matras)
    "/System/Library/Fonts/Supplemental/DevanagariMT.ttc",
    "/Users/ramdudeja/Desktop/Hindi-video-generator/fonts/NotoSansDevanagari-Regular.ttf",
    "/Library/Fonts/NotoSansDevanagari-Regular.ttf",
]

def _get_hindi_font(size: int):
    """Return a PIL font that covers both Devanagari and Latin glyphs."""
    from PIL import ImageFont
    for path in BROAD_FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _scaled_font_size(text: str, base: int) -> int:
    """Scale font size down for longer lines."""
    n = len(text)
    if n > 80:
        return 32
    if n > 60:
        return 36
    if n > 40:
        return 40
    return base


def _render_with_playwright(text: str, output_path: str, font_size: int) -> bool:
    """
    Primary renderer: headless Chromium via Playwright.
    Chrome uses HarfBuzz for text shaping, so Devanagari matras are placed
    correctly AND Latin/English characters are rendered via CSS font fallback.

    Install once with:
        pip install playwright
        playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [INFO] Playwright not installed — run: pip install playwright && playwright install chromium")
        return False

    fs = _scaled_font_size(text, font_size)

    # Build @font-face URI from the first font file found on disk
    hindi_font_uri = ""
    for fp in HINDI_FONT_PATHS:
        if os.path.exists(fp):
            hindi_font_uri = Path(fp).as_uri()
            break

    font_face_rule = (
        f"@font-face {{ font-family: 'DevFont'; src: url('{hindi_font_uri}'); }}"
        if hindi_font_uri else ""
    )
    font_family = (
        "'DevFont', 'Noto Sans Devanagari', 'Kohinoor Devanagari', "
        "'DevanagariMT', 'Arial Unicode MS', 'Noto Sans', sans-serif"
    )

    import html as _html
    safe_text = _html.escape(text)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: {VIDEO_W}px;
    height: {VIDEO_H}px;
    background: transparent;
    overflow: hidden;
  }}
  {font_face_rule}
  .box {{
    position: absolute;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    max-width: 84%;
    background: rgba(0, 0, 0, 0.78);
    border-radius: 12px;
    padding: 22px 52px;
    text-align: center;
    word-wrap: break-word;
  }}
  .text {{
    font-family: {font_family};
    font-size: {fs}px;
    color: #ffffff;
    line-height: 1.6;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.9), -1px -1px 3px rgba(0,0,0,0.7);
  }}
  .watermark {{
    position: absolute;
    bottom: 28px;
    right: 32px;
    font-family: Arial, sans-serif;
    font-size: 18px;
    color: rgba(180, 180, 180, 0.7);
  }}
</style>
</head>
<body>
  <div class="box"><div class="text">{safe_text}</div></div>
  <div class="watermark">{WATERMARK}</div>
</body>
</html>"""

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": VIDEO_W, "height": VIDEO_H})
            page.set_content(html_content, wait_until="domcontentloaded")
            page.screenshot(
                path=str(output_path),
                type="png",
                omit_background=True,
                full_page=False,
            )
            browser.close()
        return True
    except Exception as e:
        print(f"  [PLAYWRIGHT ERROR] {e}")
        return False


def _render_with_pillow(text: str, output_path: str, font_size: int) -> bool:
    """
    Fallback renderer using Pillow.
    Uses Arial Unicode MS so Latin/English characters are visible.
    Matra placement may still be imperfect without libraqm — install Playwright
    for pixel-perfect Devanagari.
    """
    from PIL import ImageDraw, ImageFont

    fs = _scaled_font_size(text, font_size)

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = _get_hindi_font(fs)

        chars_per_line = max(20, int(VIDEO_W * 0.80 / (fs * 0.55)))
        lines = textwrap.wrap(text, width=chars_per_line) or [text]

        line_height = int(fs * 1.55)
        total_text_h = len(lines) * line_height
        pad_x, pad_y = 60, 20

        max_line_w = max(
            (draw.textbbox((0, 0), ln, font=font)[2] - draw.textbbox((0, 0), ln, font=font)[0])
            for ln in lines
        )
        box_w = min(max_line_w + pad_x * 2, VIDEO_W - 40)
        box_h = total_text_h + pad_y * 2
        box_x = (VIDEO_W - box_w) // 2
        box_y = VIDEO_H - box_h - 80

        overlay = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=12, fill=(0, 0, 0, 190)
        )
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        y = box_y + pad_y
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            x = (VIDEO_W - (bb[2] - bb[0])) // 2
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        wm_font = _get_hindi_font(18)
        draw.text((VIDEO_W - 200, VIDEO_H - 46), WATERMARK,
                  font=wm_font, fill=(150, 150, 150, 178))

        img.save(str(output_path), "PNG")
        return True

    except Exception as e:
        print(f"  [PILLOW RENDER ERROR] {e}")
        return False


def render_text_with_chrome(text: str, output_path: str, font_size: int = 44,
                            bg_r: int = 15, bg_g: int = 20, bg_b: int = 45) -> bool:
    """
    Render subtitle text.
    1. Tries Playwright/headless-Chrome (correct HarfBuzz matra shaping + Latin support).
    2. Falls back to Pillow with Arial Unicode MS (Latin visible; matras best-effort).
    """
    if _render_with_playwright(text, output_path, font_size):
        return True
    return _render_with_pillow(text, output_path, font_size)

# ── Article parsing ─────────────────────────────────────────────────────────────
def parse_sections(filepath):
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()
    
    sections = []
    lines = raw.split('\n')
    current_title = None
    current_body = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            if current_title:
                body = ' '.join(current_body).strip()
                if body:
                    sections.append({"title": current_title, "body": body})
            current_title = re.sub(r'^#+\s*', '', line).strip()
            current_body = []
        else:
            if current_title is None:
                current_title = "Introduction"
            current_body.append(line)
    
    if current_title and current_body:
        body = ' '.join(current_body).strip()
        if body:
            sections.append({"title": current_title, "body": body})
    
    return sections

def split_sentences(text):
    parts = re.split(r'(?<=[।])\s+', text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 4]

# ── Voice check ─────────────────────────────────────────────────────────────────
def check_voice():
    global TTS_VOICE
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    available = result.stdout.lower()
    if TTS_VOICE.lower() in available:
        print(f"  [VOICE] '{TTS_VOICE}' found")
        return True
    if "lekha" in available:
        TTS_VOICE = "Lekha"
        print(f"  [VOICE] Falling back to 'Lekha'")
        return True
    print("  [VOICE] No Hindi voice found, using default")
    return False

# ── TTS Generation ─────────────────────────────────────────────────────────────
def generate_audio_sarvam(text: str, output_path: str) -> float:
    import requests
    
    for attempt in range(3):
        try:
            response = requests.post(
                SARVAM_TTS_URL,
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "target_language_code": "hi-IN",
                    "speaker": "shubh",
                    "model": "bulbul:v3",
                    "pace": 1.0,
                    "speech_sample_rate": 22050,
                    "output_audio_codec": "mp3",
                    "enable_preprocessing": True
                },
                timeout=120
            )
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                dur = get_duration(output_path)
                print(f"    [SARVAM] {dur:.1f}s")
                return dur
            else:
                print(f"    [SARVAM] Error {response.status_code}")
        except Exception as e:
            print(f"    [SARVAM] Attempt {attempt+1}: {e}")
    
    return generate_audio_macos(text, output_path)

def generate_audio_macos(text: str, output_path: str) -> float:
    audio_dir = Path(output_path).parent.resolve()
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    stem = Path(output_path).stem
    aiff = audio_dir / f"temp_{stem}.aiff"
    txt = audio_dir / f"temp_{stem}.txt"
    
    txt.write_text(text, encoding="utf-8")
    
    try:
        subprocess.run([
            "say", "-r", str(TTS_RATE), "-o", str(aiff),
            "-f", str(txt), "-v", TTS_VOICE
        ], check=True, capture_output=True)
        
        subprocess.run([
            "ffmpeg", "-y", "-i", str(aiff),
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-ac", "2",
            str(output_path)
        ], check=True, capture_output=True)
        
        aiff.unlink(missing_ok=True)
        txt.unlink(missing_ok=True)
        
        dur = get_duration(output_path)
        return dur
    except Exception as e:
        print(f"    [MACOS TTS] Error: {e}")
        return 3.0

def generate_audio(text: str, idx: int, use_sarvam: bool = True) -> tuple:
    mp3_path = AUDIO_DIR / f"audio_{idx:04d}.mp3"
    
    if mp3_path.exists():
        return mp3_path, get_duration(mp3_path)
    
    if use_sarvam and not ARGS.no_sarvam:
        dur = generate_audio_sarvam(text, str(mp3_path))
    else:
        dur = generate_audio_macos(text, str(mp3_path))
    
    return mp3_path, dur

def get_duration(path) -> float:
    if not path or not Path(path).exists():
        return 3.0
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 3.0

# ── Background Image ─────────────────────────────────────────────────────────────
def create_base_background():
    """Create gradient background."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (15, 20, 45))
    return img

def load_and_prepare_bg_image(image_path: str) -> Image.Image:
    """Load background image, scale to cover 1920x1080."""
    img = Image.open(image_path).convert("RGB")
    orig_w, orig_h = img.size
    
    target_ratio = VIDEO_W / VIDEO_H
    orig_ratio = orig_w / orig_h
    
    if orig_ratio > target_ratio:
        new_h = VIDEO_H
        new_w = int(new_h * orig_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - VIDEO_W) // 2
        img = img.crop((left, 0, left + VIDEO_W, VIDEO_H))
    else:
        new_w = VIDEO_W
        new_h = int(new_w / orig_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - VIDEO_H) // 2
        img = img.crop((0, top, VIDEO_W, top + VIDEO_H))
    
    return img

# ── Video clip creation with Chrome text ────────────────────────────────────────
def create_clip_with_chrome_text(
    bg_image: Optional[Image.Image],
    audio_path: str,
    text: str,
    idx: int
) -> Optional[Path]:
    """Create video clip using Chrome for text rendering."""
    out = CLIPS_DIR / f"clip_{idx:04d}.mp4"
    if out.exists():
        return out
    
    dur = get_duration(audio_path)
    
    # Render text with Python/Pillow
    text_img_path = TEXT_IMG_DIR / f"text_{idx:04d}.png"
    if not text_img_path.exists():
        # Use a dark semi-transparent background for the text
        # This ensures text is readable on any background
        success = render_text_with_chrome(
            text, 
            str(text_img_path),
            font_size=44
        )
        
        if not success:
            print(f"  [CHROME] Failed to render text, using fallback")
            # Create a fallback text image with Pillow
            create_fallback_text_image(text, text_img_path)
    
    # Create composite image: background + text
    if bg_image:
        frame = bg_image.copy()
    else:
        frame = create_base_background()
    
    # Overlay text image (text has its own dark background)
    if text_img_path.exists():
        text_img = Image.open(str(text_img_path)).convert("RGBA")
        frame.paste(text_img, (0, 0), text_img)
    
    # Save composite frame
    frame_path = OUTPUT_DIR / f"frame_{idx:04d}.png"
    frame.save(str(frame_path), "PNG")
    
    # Create video from frame + audio
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(frame_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        "-t", str(dur),
        "-shortest",
        str(out)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    [FFMPEG Error]: {result.stderr[-300:]}")
            return None
        
        # Cleanup
        frame_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"    [Error]: {e}")
        return None
    
    return out

def create_fallback_text_image(text: str, output_path: Path):
    """Last-resort fallback using Pillow with broad-coverage font."""
    _render_with_pillow(text, str(output_path), font_size=44)

# ── Concatenate clips ───────────────────────────────────────────────────────────
def concatenate(clips):
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast",
        "-crf", str(CRF),
        "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        str(FINAL_VIDEO)
    ]
    
    print(f"  [MERGE] Combining {len(clips)} clips...")
    subprocess.run(cmd, check=True, capture_output=True)
    concat_file.unlink(missing_ok=True)
    return FINAL_VIDEO

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Hindi Video Generator V13 - Python Text Rendering")
    print("  Uses Pillow for Devanagari text (no Chrome/Node needed)")
    print("=" * 70)
    
    ensure_dirs()
    
    use_sarvam = not ARGS.no_sarvam
    if use_sarvam:
        print(f"  [TTS] Sarvam AI (shubh voice)")
    else:
        check_voice()
        print(f"  [TTS] macOS {TTS_VOICE}")
    
    # Load background image if provided (or use default)
    bg_path = ARGS.bg_image if ARGS.bg_image else DEFAULT_BG_IMAGE
    bg_img = None
    if bg_path:
        if bg_path.startswith("http"):
            import urllib.request
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                urllib.request.urlretrieve(bg_path, tmp.name)
                bg_img = load_and_prepare_bg_image(tmp.name)
                os.unlink(tmp.name)
        else:
            bg_img = load_and_prepare_bg_image(bg_path)
        print(f"  [BG] Background image loaded: {bg_img.size}")
    else:
        print(f"  [BG] No background image selected, using gradient")
    
    # Parse article
    print("\n[1/4] Parsing article...")
    sections = parse_sections(str(ARTICLE_FILE))
    print(f"      {len(sections)} sections found")
    
    total_sentences = sum(len(split_sentences(s["body"])) for s in sections)
    print(f"      {total_sentences} sentences total")
    
    print("\n[2/4] Generating clips with Python text rendering...")
    all_clips = []
    idx = 0
    total_dur = 0.0
    
    for sec_idx, section in enumerate(sections):
        sentences = split_sentences(section["body"])
        
        if ARGS.short:
            sentences = sentences[:MAX_SENTENCES_SHORT]
        
        print(f"\n  ── Sec {sec_idx+1}: {section['title'][:40]} [{len(sentences)} sentences]")
        
        for sent in sentences:
            if len(sent) < 4:
                continue
            
            # Generate audio
            audio, dur = generate_audio(sent, idx, use_sarvam)
            total_dur += dur
            
            # Create clip with Chrome text
            clip = create_clip_with_chrome_text(bg_img, str(audio), sent, idx)
            if clip:
                all_clips.append(clip)
                print(f"    [{idx:3d}] {dur:4.1f}s | {sent[:55]}...")
            
            idx += 1
    
    print(f"\n[3/4] Concatenating {len(all_clips)} clips...")
    final = concatenate(all_clips)
    
    mins, secs = divmod(int(total_dur), 60)
    size_mb = os.path.getsize(final) / (1024 * 1024) if final.exists() else 0
    
    print("\n" + "=" * 70)
    print(f"  ✅ Video ready!")
    print(f"      File: {final}")
    print(f"      Size: {size_mb:.1f} MB")
    print(f"      Clips: {len(all_clips)}")
    print(f"      Duration: ~{mins}m {secs}s")
    print(f"      Resolution: {VIDEO_W}x{VIDEO_H}")
    print(f"      Frame rate: {FPS}fps")
    print("=" * 70)
    
    return final

if __name__ == "__main__":
    main()
