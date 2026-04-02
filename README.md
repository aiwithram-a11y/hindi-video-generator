# Hindi Video Generator

Generate narrated Hindi videos from articles with proper Devanagari text rendering.

## Features

- **Proper Hindi Text Rendering** - Uses Chrome/Browser engine for correct Devanagari matra shaping
- **High Quality TTS** - Uses Sarvam AI for natural Hindi voice synthesis
- **Customizable** - Configurable video quality, background images, and fonts
- **Batch Processing** - Automatically splits articles into sentences and creates video clips

## Why Chrome for Text Rendering?

Hindi (Devanagari) uses complex text layout where vowel matras (like ी, ू, ें, ै) appear before their consonants in memory but after them when spoken. This requires sophisticated text shaping that browsers handle via HarfBuzz, but most image processing libraries like Pillow cannot.

This generator uses Chrome/Puppeteer to render text, ensuring all matras display correctly.

## Installation

### Prerequisites

- macOS or Linux
- Python 3.9+
- Node.js (for Chrome text rendering)
- Google Chrome or Chromium
- FFmpeg

### Setup

```bash
# Clone the repository
git clone https://github.com/ramkrishan/hindi-video-generator.git
cd hindi-video-generator

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for Chrome rendering)
npm install
```

### Fonts

The script uses Chrome's built-in Noto Sans Devanagari font. For best results, ensure Chrome is installed.

## Usage

### Basic Usage

```bash
python generate_video.py --article path/to/article.md
```

### With Background Image

```bash
python generate_video.py \
  --article path/to/article.md \
  --bg-image path/to/image.jpg \
  --output-dir output_folder
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--article` | Path to article markdown file | Required |
| `--output-dir` | Output directory | `./output` |
| `--bg-image` | Background image (local path or URL) | None (gradient background) |
| `--crf` | Video quality (lower = better, 18-28) | 20 |
| `--short` | Generate short version (first 2 sentences per section) | False |
| `--no-sarvam` | Use macOS TTS instead of Sarvam AI | False |

### Example

```bash
# Generate video from article
python generate_video.py \
  --article examples/sample_article.md \
  --bg-image https://example.com/background.jpg \
  --output-dir ./my_video \
  --crf 20
```

## Article Format

Articles should be in Markdown format with headings:

```markdown
# Title

## Section 1

Content of section 1 in Hindi. This will be split into sentences.

## Section 2

More content here.
```

## Output

The generator creates:

```
output/
├── audio/              # TTS audio files
│   └── audio_0000.mp3
│   └── audio_0001.mp3
│   └── ...
├── clips/              # Individual video clips
│   └── clip_0000.mp4
│   └── clip_0001.mp4
│   └── ...
├── final_video.mp4     # Final concatenated video
└── concat.txt          # FFmpeg concat list
```

## How It Works

1. **Parse Article** - Split markdown into sections and sentences
2. **Generate TTS** - Convert each sentence to audio using Sarvam AI
3. **Render Text** - Use Chrome to render Hindi text with proper Devanagari shaping
4. **Create Clips** - Combine background + text + audio into video clips
5. **Concatenate** - Merge all clips into final video

## API Keys

The script uses Sarvam AI for TTS. Get your API key from [Sarvam AI](https://sarvam.ai) and set it in the script:

```python
SARVAM_API_KEY = "your-api-key"
```

## Troubleshooting

### Text Rendering Issues

If Hindi text doesn't render correctly (missing matras, rectangles):
- Ensure Chrome is installed
- Verify Node.js and puppeteer are installed
- Check that `/tmp/render_hindi.js` exists

### Audio Issues

If TTS fails:
- Check your Sarvam API key
- Ensure internet connection
- Use `--no-sarvam` flag to fall back to macOS TTS

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
