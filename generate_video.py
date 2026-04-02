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
TTS_VOICE = "Tara"
TTS_RATE = 158
CRF = 20

# Default background image
DEFAULT_BG_IMAGE = "/Users/ramdudeja/Desktop/Claud_work_Folder/image.jpeg"

# Path to Puppeteer renderer (relative to script location)
SCRIPT_DIR = Path(__file__).parent.resolve()
PUPPETEER_SCRIPT = SCRIPT_DIR / "src" / "render_hindi.js"

# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Hindi Video Generator V13 - Chrome Text")
    p.add_argument("--article", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--bg-image", default=None, help="Background image (local or URL)")
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

# ── Chrome Text Renderer ───────────────────────────────────────────────────────
def render_text_with_chrome(text: str, output_path: str, font_size: int = 44, 
                            bg_r: int = 15, bg_g: int = 20, bg_b: int = 45) -> bool:
    """
    Render Hindi text using Chrome/Puppeteer for proper Devanagari shaping.
    Returns True if successful, False otherwise.
    """
    # Escape text for HTML
    html_escaped = (text
                    .replace('\\', '\\\\')
                    .replace('"', '\\"')
                    .replace("'", "\\'")
                    .replace('\n', '<br>'))
    
    # Calculate font size based on text length
    if len(text) > 80:
        fs = 32
    elif len(text) > 60:
        fs = 36
    elif len(text) > 40:
        fs = 40
    else:
        fs = font_size
    
    cmd = [
        "node", "-e", f"""
const {{ renderText }} = require('{PUPPETEER_SCRIPT}');
(async () => {{
    await renderText({{
        text: "{html_escaped}",
        outputPath: "{output_path}",
        fontSize: {fs},
        bgR: {bg_r},
        bgG: {bg_g},
        bgB: {bg_b}
    }});
}})();
"""
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"  [CHROME ERROR] {e}")
        return False

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
    
    # Render text with Chrome
    text_img_path = TEXT_IMG_DIR / f"text_{idx:04d}.png"
    if not text_img_path.exists():
        # Use background image colors for the text renderer's background
        if bg_image:
            # Sample center pixel for background color
            px = bg_image.getpixel((VIDEO_W // 2, VIDEO_H // 2))
            bg_r, bg_g, bg_b = int(px[0] * 0.6), int(px[1] * 0.6), int(px[2] * 0.6)
        else:
            bg_r, bg_g, bg_b = 15, 20, 45
        
        success = render_text_with_chrome(
            text, 
            str(text_img_path),
            font_size=44,
            bg_r=bg_r, bg_g=bg_g, bg_b=bg_b
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
    
    # Darken background slightly
    dark = Image.new("RGB", frame.size, (0, 0, 0))
    frame = Image.blend(frame, dark, 0.15)
    
    # Overlay text image
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
    """Fallback text image using Pillow (for when Chrome fails)."""
    from PIL import ImageDraw, ImageFont
    
    img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to find a font
    font = None
    for path, idx in [
        ("/System/Library/Fonts/Supplemental/DevanagariMT.ttc", 0),
        ("/System/Library/Fonts/Kohinoor.ttc", 0),
    ]:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 44, index=idx)
                break
            except:
                continue
    
    if font is None:
        font = ImageFont.load_default()
    
    lines = textwrap.wrap(text, width=35)
    y = VIDEO_H - 150
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (VIDEO_W - (bbox[2] - bbox[0])) // 2
        # Draw outline
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        # Draw white text
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += 70
    
    img.save(str(output_path), "PNG")

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
    print("  Hindi Video Generator V13 - Chrome Text Rendering")
    print("  Uses Chrome for proper Devanagari matra shaping")
    print("=" * 70)
    
    ensure_dirs()
    
    use_sarvam = not ARGS.no_sarvam
    if use_sarvam:
        print(f"  [TTS] Sarvam AI (shubh voice)")
    else:
        check_voice()
        print(f"  [TTS] macOS {TTS_VOICE}")
    
    # Load background image if provided (or use default)
    bg_img = None
    bg_path = ARGS.bg_image if ARGS.bg_image else DEFAULT_BG_IMAGE
    
    if bg_path and os.path.exists(bg_path):
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
        print(f"  [BG] No background image found, using gradient")
    
    # Parse article
    print("\n[1/4] Parsing article...")
    sections = parse_sections(str(ARTICLE_FILE))
    print(f"      {len(sections)} sections found")
    
    total_sentences = sum(len(split_sentences(s["body"])) for s in sections)
    print(f"      {total_sentences} sentences total")
    
    print("\n[2/4] Generating clips with Chrome text rendering...")
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
