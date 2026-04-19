#!/usr/bin/env node
/**
 * PDF Text Adder - Add Hindi text below "Fake vs Fact" 
 * Matches the original PDF design
 */

const fs = require('fs');
const path = require('path');

const BASE = '/Users/ramdudeja/Desktop/Hindi-video-generator';
const PDF_PATH = '/Users/ramdudeja/Downloads/RayNews FakeVsFact Concept copy.pdf';

// Hindi text to add
const HINDI_LINE1 = "रोज़ एक नया सच - जब दुनिया झूठी ख़बर पर विश्वास करे।";
const HINDI_LINE2 = "हम आपको बतायेंगे असली हक़ीक़त!";

// Convert PDF to base64 for inline embedding
// Since PDF can't be embedded directly, we'll create HTML overlay

const html = `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { 
  width: 1080px; 
  height: 1080px; 
  background: #0d1b2a;
  position: relative;
  font-family: 'Noto Sans Devanagari', 'Kohinoor Devanagari', sans-serif;
  overflow: hidden;
}
/* Original PDF elements */
.logo {
  position: absolute;
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, #e63946, #ff6b6b);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 30px rgba(230,57,70,0.4);
}
.logo-inner {
  width: 120px;
  height: 120px;
  border: 4px solid white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-text {
  color: white;
  font-size: 50px;
  font-weight: 900;
}
.headline-main {
  position: absolute;
  top: 210px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}
.headline-text {
  display: block;
  color: white;
  font-size: 42px;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1.4;
}
/* FAKE vs FACT - Original position preserved */
.fake-fact-container {
  position: absolute;
  top: 380px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 30px;
  background: linear-gradient(90deg, #e63946, #ff6b6b);
  padding: 20px 50px;
  border-radius: 15px;
}
.fake, .fact {
  color: white;
  font-size: 60px;
  font-weight: 900;
  letter-spacing: 2px;
}
.vs {
  color: white;
  font-size: 36px;
  font-weight: 400;
  opacity: 0.9;
}
/* NEW HINDI TEXT - Just below Fake vs Fact */
.hindi-text-container {
  position: absolute;
  top: 500px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  width: 900px;
}
.hindi-line1 {
  color: #4fc3f7;
  font-size: 24px;
  font-weight: 600;
  display: block;
  margin-bottom: 10px;
}
.hindi-line2 {
  color: #81c784;
  font-size: 22px;
  font-weight: 500;
  display: block;
}
/* Stats section */
.stats-container {
  position: absolute;
  top: 620px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 80px;
}
.stat-box {
  text-align: center;
}
.stat-number {
  color: white;
  font-size: 48px;
  font-weight: 800;
}
.stat-label {
  color: rgba(255,255,255,0.7);
  font-size: 16px;
  margin-top: 5px;
}
/* Bottom CTA */
.cta-container {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}
.cta-text {
  color: #4fc3f7;
  font-size: 28px;
  font-weight: 600;
}
.cta-sub {
  color: rgba(255,255,255,0.6);
  font-size: 18px;
  margin-top: 10px;
}
</style>
</head>
<body>
<div class="logo">
  <div class="logo-inner">
    <span class="logo-text">R</span>
  </div>
</div>

<div class="headline-main">
  <span class="headline-text">रेडियो पर सुनें</span>
  <span class="headline-text">सच्चाई का असली सच</span>
</div>

<div class="fake-fact-container">
  <span class="fake">FAKE</span>
  <span class="vs">vs</span>
  <span class="fact">FACT</span>
</div>

<!-- NEW HINDI TEXT - Added below Fake vs Fact -->
<div class="hindi-text-container">
  <span class="hindi-line1">${HINDI_LINE1}</span>
  <span class="hindi-line2">${HINDI_LINE2}</span>
</div>

<div class="stats-container">
  <div class="stat-box">
    <span class="stat-number">10+</span>
    <div class="stat-label">Lakh Views</div>
  </div>
  <div class="stat-box">
    <span class="stat-number">50K+</span>
    <div class="stat-label">Subscribers</div>
  </div>
  <div class="stat-box">
    <span class="stat-number">100+</span>
    <div class="stat-label">Episodes</div>
  </div>
</div>

<div class="cta-container">
  <div class="cta-text">📺 YouTube | 🎙️ Spotify | 📻 Radio</div>
  <div class="cta-sub">Follow RayNews for real news</div>
</div>
</body></html>`;

const htmlPath = path.join(BASE, 'fake_vs_fact_with_hindi.html');
fs.writeFileSync(htmlPath, html);

console.log('=== HTML with Hindi text created ===');
console.log('File:', htmlPath);
console.log('\n--- Commands ---');
console.log('chrome-devtools_new_page "file://' + htmlPath + '"');
console.log('chrome-devtools_take_screenshot filePath="' + path.join(BASE, 'fake_vs_fact_output.png') + '"');