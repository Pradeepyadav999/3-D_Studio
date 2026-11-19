import puppeteer from 'puppeteer-core';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const ARTIFACTS_DIR = '/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-shoulder-test-v2',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1050 }
  });

  try {
    const page = await browser.newPage();
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(2000);

    // 1. TEST ALLEN SOLLY POLO
    console.log('Testing Allen Solly Polo...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const sampleBtn = btns.find(b => b.innerText && b.innerText.includes('Try Samples'));
      if (sampleBtn) sampleBtn.click();
    });
    await sleep(1000);

    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const poloBtn = buttons.find(b => b.innerText && b.innerText.includes('Allen Solly'));
      if (poloBtn) poloBtn.click();
    });
    await sleep(1000);

    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && b.innerText.includes('Generate 3D Garment'));
      if (genBtn) genBtn.click();
    });

    console.log('Waiting for Polo generation...');
    await page.waitForFunction(() => {
      const txt = document.body.innerText;
      return txt.includes('POLYGONS') || txt.includes('Polygons:') || txt.includes('3D MODEL & TEXTURE ASSETS');
    }, { timeout: 40000 });
    await sleep(2500);

    // Polo Solid Front
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.innerText && b.innerText.trim() === 'SOLID');
      if (btn) btn.click();
      const frontBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Front');
      if (frontBtn) frontBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_polo_solid_front.png` });

    // Polo Solid Perspective
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const perspBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Perspective');
      if (perspBtn) perspBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_polo_solid_persp.png` });

    // Polo Solid + Wire Top
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const wireBtn = btns.find(b => b.innerText && b.innerText.trim().includes('SOLID + WIRE'));
      if (wireBtn) wireBtn.click();
      const topBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Top');
      if (topBtn) topBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_polo_wire_top.png` });

    // 2. TEST ROADSTER CREW NECK
    console.log('Testing Roadster Crew Neck...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const blackProduct = buttons.find(b => b.innerText && (b.innerText.includes('Onyx Black') || b.innerText.includes('Pacific Coastline') || b.innerText.includes('Black')));
      if (blackProduct) blackProduct.click();
    });
    await sleep(1000);

    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && b.innerText.includes('Generate 3D Garment'));
      if (genBtn) genBtn.click();
    });

    console.log('Waiting for Crew generation...');
    await page.waitForFunction(() => {
      const txt = document.body.innerText;
      return txt.includes('POLYGONS') || txt.includes('Polygons:') || txt.includes('3D MODEL & TEXTURE ASSETS');
    }, { timeout: 40000 });
    await sleep(2500);

    // Crew Textured Front
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const texBtn = btns.find(b => b.innerText && b.innerText.trim().includes('TEXTURED'));
      if (texBtn) texBtn.click();
      const frontBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Front');
      if (frontBtn) frontBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_crew_textured_front.png` });

    // Crew Solid Perspective
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const solidBtn = btns.find(b => b.innerText && b.innerText.trim() === 'SOLID');
      if (solidBtn) solidBtn.click();
      const perspBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Perspective');
      if (perspBtn) perspBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_crew_solid_persp.png` });

    // Crew Solid + Wire Top
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const wireBtn = btns.find(b => b.innerText && b.innerText.trim().includes('SOLID + WIRE'));
      if (wireBtn) wireBtn.click();
      const topBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Top');
      if (topBtn) topBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/fixed_crew_wire_top.png` });

    console.log('All verification screenshots captured successfully!');
  } finally {
    await browser.close();
  }
}

run().catch(console.error);
