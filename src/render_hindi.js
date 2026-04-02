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
        bgR = 15,
        bgG = 20,
        bgB = 45
    } = options;

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
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
body {
    background: rgb(${bgR}, ${bgG}, ${bgB});
    width: ${width}px;
    height: ${height}px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
    padding-bottom: 100px;
    font-family: 'Noto Sans Devanagari', 'Kohinoor Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.text-container {
    text-align: center;
    max-width: 1800px;
    padding: 0 60px;
}
.subtitle {
    color: white;
    font-size: ${fontSize}px;
    line-height: 1.6;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.9), -1px -1px 4px rgba(0,0,0,0.9);
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
