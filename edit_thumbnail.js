/**
 * Thumbnail Text Editor
 * Run: node ~/Desktop/Hindi-video-generator/edit_thumbnail.js
 *
 * The script will ask you for:
 *   - Input image path
 *   - Output image path
 *   - Title text (Hindi)
 *   - Subtitle text (Hindi)
 */

const fs       = require('fs');
const path     = require('path');
const readline = require('readline');

const HOME = process.env.HOME;
const BASE = path.join(HOME, 'Desktop/Hindi-video-generator');

// Tell Puppeteer to use system Chrome — prevents download/validation hang
process.env.PUPPETEER_EXECUTABLE_PATH =
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
process.env.PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = 'true';

// ── readline helpers ────────────────────────────────────────────────────────
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

function ask(question, defaultVal) {
  return new Promise(resolve => {
    rl.question(`${question} [${defaultVal}]: `, answer => {
      resolve(answer.trim() || defaultVal);
    });
  });
}

// ── Main ───────────────────────────────────────────────────────────────────
(async () => {
  console.log('\nThumbnail Text Editor\n');

  const INPUT    = await ask('Input image  ', path.join(BASE, 'thumbnail1.png'));
  const OUTPUT   = await ask('Output image ', path.join(BASE, 'thumbnail_out.jpg'));
  const TITLE    = await ask('Title text   ', 'डिजिटल अरेस्ट');
  const SUBTITLE = await ask('Subtitle text', 'आपके खाते से पैसा गायब!');
  rl.close();

  const inputPath  = INPUT.replace(/^~/, HOME);
  const outputPath = OUTPUT.replace(/^~/, HOME);

  console.log('\n[INPUT]   ', inputPath);
  console.log('[OUTPUT]  ', outputPath);
  console.log('[TITLE]   ', TITLE);
  console.log('[SUBTITLE]', SUBTITLE, '\n');

  // Load puppeteer AFTER readline (avoids hang on startup)
  console.log('[INFO]    Loading browser...');
  const PUPPETEER_PATHS = [
    path.join(BASE, 'node_modules/puppeteer'),
    path.join(HOME, 'node_modules/puppeteer'),
  ];
  let puppeteer = null;
  for (const p of PUPPETEER_PATHS) {
    if (fs.existsSync(p)) { puppeteer = require(p); break; }
  }
  if (!puppeteer) { console.error('ERROR: Puppeteer not found.'); process.exit(1); }

  // Find system Chrome
  const CHROME_PATHS = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
  ];
  let executablePath = null;
  for (const p of CHROME_PATHS) {
    if (fs.existsSync(p)) { executablePath = p; break; }
  }
  if (!executablePath) { console.error('ERROR: Chrome not found.'); process.exit(1); }
  console.log('[CHROME]  ', executablePath);

  // Embed image as base64
  const ext    = path.extname(inputPath).toLowerCase();
  const mime   = ext === '.png' ? 'image/png' : 'image/jpeg';
  const imgB64 = fs.readFileSync(inputPath).toString('base64');
  const imgSrc = `data:${mime};base64,${imgB64}`;
  console.log('[IMAGE]   Loaded', (imgB64.length / 1024).toFixed(0), 'KB');

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin:0; padding:0; }
  body { width:1536px; height:1024px; overflow:hidden; position:relative; background:#000; }
  .bg  { position:absolute; top:0; left:0; width:1536px; height:1024px; object-fit:cover; }
  .cover {
    position:absolute; left:0; top:580px;
    width:850px; height:330px;
    background:#180450;
  }
  .title {
    position:absolute; left:45px; top:605px;
    font-family:'Kohinoor Devanagari','Devanagari MT','ITF Devanagari',sans-serif;
    font-size:100px; font-weight:700; color:#fff;
    text-shadow: 3px 3px 0 #000,-3px 3px 0 #000,3px -3px 0 #000,-3px -3px 0 #000;
    white-space:nowrap;
  }
  .sub {
    position:absolute; left:45px; top:740px;
    font-family:'Kohinoor Devanagari','Devanagari MT','ITF Devanagari',sans-serif;
    font-size:56px; font-weight:600; color:#FFD700;
    text-shadow: 2px 2px 0 #000,-2px 2px 0 #000,2px -2px 0 #000,-2px -2px 0 #000;
    white-space:nowrap;
  }
</style>
</head>
<body>
  <img class="bg" src="${imgSrc}">
  <div class="cover"></div>
  <div class="title">${TITLE}</div>
  <div class="sub">${SUBTITLE}</div>
</body>
</html>`;

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1536, height: 1024 });
    await page.setContent(html, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.evaluate(() => document.fonts.ready);
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: outputPath, type: 'jpeg', quality: 95 });
    console.log(`\nSaved -> ${outputPath}  (${(fs.statSync(outputPath).size/1024).toFixed(0)} KB)\n`);
  } finally {
    await browser.close();
  }

})().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
