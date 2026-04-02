#!/bin/bash
# Setup script for Hindi Video Generator

set -e

echo "🔧 Setting up Hindi Video Generator..."

# Check Python version
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  python generate_video.py --article examples/sample_article.md"
