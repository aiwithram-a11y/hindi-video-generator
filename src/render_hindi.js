#!/usr/bin/env node
/**
 * Hindi Text Renderer using Puppeteer (Chrome)
 * Renders Hindi text with proper Devanagari shaping
 * 
 * IMPORTANT: Uses transparent background - composited later with background image
 */

const puppeteer = require('puppeteer');
const path = require('path');

async function renderText(options) {
    const {
        text,
        outputPath,
        fontSize = 44,
        width = 1920,
        height = 1080
    } = options;

    const browser = await puppeteer.launch({
        headless: 'new',
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });

    const html = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
    background: transparent;
    width: ${width}px;
    height: ${height}px;
    overflow: hidden;
}
body {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    padding-bottom: 80px;
    font-family: 'Noto Sans Devanagari', 'Kohinoor Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.text-container {
    text-align: center;
    max-width: 1800px;
    padding: 20px 60px;
    background: rgba(0, 0, 0, 0.75);
    border-radius: 12px;
}
.subtitle {
    color: white;
    font-size: ${fontSize}px;
    line-height: 1.6;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}
.watermark {
    position: fixed;
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

    await page.setContent(html, { waitUntil: 'domcontentloaded', timeout: 60000 });
    
    // Short wait for fonts
    await new Promise(resolve => setTimeout(resolve, 200));

    // Take screenshot with transparent background
    await page.screenshot({
        path: outputPath,
        type: 'png',
        omitBackground: true
    });

    await browser.close();
    console.log(`Rendered: ${outputPath}`);
}

module.exports = { renderText };
