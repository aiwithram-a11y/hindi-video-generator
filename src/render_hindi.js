#!/usr/bin/env node
/**
 * Hindi Text Renderer using Puppeteer (Chrome)
 * Renders Hindi text with proper Devanagari shaping
 */

const puppeteer = require('puppeteer');
const path = require('path');

async function renderText(options) {
    const {
        text,
        outputPath,
        fontSize = 44,
        width = 1920,
        height = 1080,
        bgR = 0,
        bgG = 0,
        bgB = 0
    } = options;

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });

    // Calculate text area position (bottom of frame)
    const textAreaTop = height - 250;
    const textAreaHeight = 200;

    const html = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: transparent;
    width: ${width}px;
    height: ${height}px;
    font-family: 'Noto Sans Devanagari', 'Kohinoor Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.text-container {
    position: absolute;
    bottom: 80px;
    left: 0;
    right: 0;
    text-align: center;
    max-width: 1800px;
    margin: 0 auto;
    padding: 20px 60px;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 10px;
}
.subtitle {
    color: white;
    font-size: ${fontSize}px;
    line-height: 1.6;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}
.watermark {
    position: absolute;
    bottom: 30px;
    right: 40px;
    color: rgba(150,150,150,0.7);
    font-size: 18px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}
</style>
</head>
<body>
<div class="text-container">
    <div class="subtitle">${text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')}</div>
</div>
<div class="watermark">ramkrishan.com</div>
</body>
</html>
    `;

    await page.setContent(html, { waitUntil: 'networkidle0' });
    
    // Wait a bit for fonts to load
    await new Promise(resolve => setTimeout(resolve, 500));

    await page.screenshot({
        path: outputPath,
        type: 'png',
        omitBackground: false
    });

    await browser.close();
    console.log(`Rendered: ${outputPath}`);
}

module.exports = { renderText };
