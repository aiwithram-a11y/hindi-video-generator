#!/usr/bin/env node
/**
 * Thumbnail Text Editor - Chrome DevTools MCP Edition
 * 
 * Generates HTML for thumbnail with text overlay.
 * Use Chrome DevTools MCP to take the screenshot.
 * 
 * Usage:
 *  TITLE="My Title" SUBTITLE="My Subtitle" node edit_thumbnail_FIXED.js
 *  node edit_thumbnail_FIXED.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get actual user home
const USER = execSync('whoami', { encoding: 'utf8' }).trim();
const HOME = '/Users/' + USER;
const BASE = path.join(HOME, 'Desktop/Hindi-video-generator');

// Get title/subtitle from env vars or use defaults
const TITLE = process.env.TITLE || 'डिजिटल अरेस्ट';
const SUB   = process.env.SUBTITLE || 'आपके खाते से पैसा गायब!';
const INPUT = process.env.INPUT || path.join(BASE, 'thumbnail1.png');
const OUTPUT = process.env.OUTPUT || path.join(BASE, 'thumbnail_out.jpg');

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Run
(async () => {
  console.log('=== Thumbnail Text Editor ===\n');
  console.log('TITLE:', TITLE);
  console.log('SUB  :', SUB);

  const inPath = INPUT.replace(/^~/, HOME);
  const outPath = OUTPUT.replace(/^~/, HOME);

  if (!fs.existsSync(inPath)) {
    console.error('ERROR: Input not found:', inPath);
    process.exit(1);
  }

  // Read image as base64
  const ext = path.extname(inPath).toLowerCase();
  const mime = ext === '.png' ? 'image/png' : 'image/jpeg';
  const imgB64 = fs.readFileSync(inPath).toString('base64');
  const imgSrc = `data:${mime};base64,${imgB64}`;

  // Generate HTML
  const html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:1536px; height:1024px; overflow:hidden; position:relative; background:#000; }
.bg { position:absolute; top:0; left:0; width:1536px; height:1024px; object-fit:cover; }
.cover { position:absolute; left:0; top:500px; width:950px; height:420px; background:#180450; }
.title { position:absolute; left:45px; top:520px; font-family:'Kohinoor Devanagari',sans-serif; font-size:60px; font-weight:700; color:#fff; text-shadow:3px 3px 0 #000; width:900px; line-height:1.2; }
.subtitle { position:absolute; left:45px; top:680px; font-family:'Kohinoor Devanagari',sans-serif; font-size:48px; font-weight:600; color:#FFD700; text-shadow:2px 2px 0 #000; }
</style>
</head><body>
<img class="bg" src="${imgSrc}">
<div class="cover"></div>
<div class="title">${esc(TITLE)}</div>
<div class="subtitle">${esc(SUB)}</div>
</body></html>`;

  const htmlPath = inPath.replace(/\.[^.]+$/, '.html');
  fs.writeFileSync(htmlPath, html);

  console.log('INPUT :', inPath);
  console.log('OUTPUT:', outPath);
  console.log('IMAGE :', (imgB64.length/1024).toFixed(0), 'KB');
  console.log('HTML  :', htmlPath);
  console.log('\n=== Next Steps ===');
  console.log('In OpenWork, use Chrome DevTools MCP:');
  console.log(`  chrome-devtools_new_page "file://${htmlPath}"`);
  console.log(`  chrome-devtools_take_screenshot filePath="${outPath}"`);
  console.log('');

})().catch(e => { console.error(e.message); process.exit(1); });