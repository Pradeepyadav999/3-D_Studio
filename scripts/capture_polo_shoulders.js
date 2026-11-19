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
      '--user-data-dir=/tmp/chrome-polo-test',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1050 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(2000);

    // Click "Try Samples"
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const sampleBtn = btns.find(b => b.innerText && b.innerText.includes('Try Samples'));
      if (sampleBtn) sampleBtn.click();
    });
    await sleep(1000);

    // Select Allen Solly Polo Green
    console.log('Selecting Allen Solly Polo...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const poloBtn = buttons.find(b => b.innerText && b.innerText.includes('Allen Solly'));
      if (poloBtn) poloBtn.click();
    });
    await sleep(1000);

    // Click Generate 3D Garment
    console.log('Generating 3D Garment...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && b.innerText.includes('Generate 3D Garment'));
      if (genBtn) genBtn.click();
    });

    console.log('Waiting for generation...');
    await page.waitForFunction(() => {
      const txt = document.body.innerText;
      return txt.includes('POLYGONS') || txt.includes('Polygons:') || txt.includes('3D MODEL & TEXTURE ASSETS');
    }, { timeout: 40000 });
    await sleep(3000);

    // Switch to SOLID mode
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const solidBtn = btns.find(b => b.innerText && b.innerText.trim().includes('SOLID') && !b.innerText.includes('+'));
      if (solidBtn) solidBtn.click();
    });
    await sleep(1000);

    await page.screenshot({ path: `${ARTIFACTS_DIR}/polo_solid_front.png` });

    // Switch to Perspective
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const perspBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Perspective');
      if (perspBtn) perspBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/polo_solid_persp.png` });

    // Switch to SOLID + WIRE
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const wireBtn = btns.find(b => b.innerText && b.innerText.trim().includes('SOLID + WIRE'));
      if (wireBtn) wireBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/polo_wire_persp.png` });

    // Switch to Top view
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const topBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Top');
      if (topBtn) topBtn.click();
    });
    await sleep(1000);
    await page.screenshot({ path: `${ARTIFACTS_DIR}/polo_wire_top.png` });

    console.log('Saved polo screenshots!');
  } finally {
    await browser.close();
  }
}

run().catch(console.error);
