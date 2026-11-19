import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');
try { fs.mkdirSync(DOCS_DIR, { recursive: true }); } catch (e) {}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('Verifying perfected geometry in browser...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1000',
      '--user-data-dir=/tmp/chrome-geom-verify',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1000 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(3500);

    // Wait if generating
    for (let i = 0; i < 15; i++) {
      const isGen = await page.evaluate(() => document.body.textContent.includes('Generating 3D Model'));
      if (!isGen) break;
      await sleep(1000);
    }
    await sleep(2500);

    // 1. Perspective View
    console.log('Capturing Perspective View...');
    await page.screenshot({ path: path.join(DOCS_DIR, 'perfected_perspective_view.png') });

    // Helper to click viewport buttons
    const clickButton = async (label) => {
      const btns = await page.$$('button');
      for (const btn of btns) {
        const text = await (await btn.getProperty('textContent')).jsonValue();
        if (text.trim() === label) {
          await btn.click();
          await sleep(1200);
          return true;
        }
      }
      return false;
    };

    // 2. Front View
    console.log('Capturing Front View...');
    await clickButton('Front');
    await page.screenshot({ path: path.join(DOCS_DIR, 'perfected_front_view.png') });

    // 3. Top View (Verifying Round Crew Neckline & Broad Shoulders)
    console.log('Capturing Top-down View...');
    await clickButton('Top');
    await page.screenshot({ path: path.join(DOCS_DIR, 'perfected_top_neck_view.png') });

    // 4. Side View (Verifying Chest Depth & Natural Profile)
    console.log('Capturing Side View...');
    await clickButton('Left');
    await page.screenshot({ path: path.join(DOCS_DIR, 'perfected_side_depth_view.png') });

    // 5. Wireframe Mode
    console.log('Capturing Wireframe Topology View...');
    await clickButton('Front');
    await clickButton('Wire');
    await page.screenshot({ path: path.join(DOCS_DIR, 'perfected_front_wireframe.png') });

    console.log('ALL VERIFICATION VIEWS CAPTURED SUCCESSFULLY!');
  } finally {
    await browser.close();
  }
}

run().catch(console.error);
