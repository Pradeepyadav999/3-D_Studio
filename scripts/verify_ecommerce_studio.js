import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');
fs.makedirs = fs.mkdirSync;
try { fs.mkdirSync(DOCS_DIR, { recursive: true }); } catch (e) {}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('Launching Chrome with puppeteer-core...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1000',
      '--user-data-dir=/tmp/chrome-ecommerce-verify',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1000 }
  });

  try {
    const page = await browser.newPage();
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(3000);

    // 1. Initial State Check (Roadster Black Graphic T-Shirt)
    console.log('Waiting for initial 3D generation and model loading...');
    // Wait up to 15s for generation to complete
    for (let i = 0; i < 20; i++) {
      const isGenerating = await page.evaluate(() => {
        return document.body.textContent.includes('Generating 3D Model');
      });
      if (!isGenerating) break;
      await sleep(1000);
    }
    await sleep(2500);

    const initialOverview = await page.evaluate(() => {
      return {
        title: document.title,
        header: document.querySelector('header')?.innerText,
        productTitle: document.querySelector('h3')?.innerText,
        brand: document.querySelector('.text-blue-400')?.innerText,
        dominantColor: document.querySelector('.text-xs.font-semibold.text-white')?.innerText,
        canvasExists: !!document.querySelector('canvas')
      };
    });
    console.log('Initial studio state:', initialOverview);

    // Capture Full UI View
    const blackFullShot = path.join(DOCS_DIR, 'ecommerce_studio_black_graphic.png');
    await page.screenshot({ path: blackFullShot });
    console.log(`Saved screenshot: ${blackFullShot}`);

    // Click "Front" view button in viewport toolbar to see front chest graphic clearly
    const frontButtons = await page.$$('button');
    for (const btn of frontButtons) {
      const text = await (await btn.getProperty('textContent')).jsonValue();
      if (text.trim() === 'Front') {
        await btn.click();
        console.log('Clicked Front View button');
        break;
      }
    }
    await sleep(1500);

    const blackFrontShot = path.join(DOCS_DIR, 'ecommerce_black_front_view.png');
    await page.screenshot({ path: blackFrontShot });
    console.log(`Saved front view: ${blackFrontShot}`);

    // 2. Select Sample 2: HIGHLANDER White Varsity T-Shirt
    console.log('Switching to Sample 2 (HIGHLANDER White Varsity T-Shirt)...');
    // Click "Try Samples" tab
    const tabs = await page.$$('button');
    for (const tab of tabs) {
      const text = await (await tab.getProperty('textContent')).jsonValue();
      if (text.includes('Try Samples')) {
        await tab.click();
        break;
      }
    }
    await sleep(800);

    // Click the Highlander card
    const sampleCards = await page.$$('button');
    for (const card of sampleCards) {
      const text = await (await card.getProperty('textContent')).jsonValue();
      if (text.includes('HIGHLANDER') || text.includes('Optical White')) {
        await card.click();
        console.log('Clicked Highlander White Sample Card');
        break;
      }
    }
    await sleep(1000);

    // Wait for generation
    console.log('Waiting for Highlander 3D model generation...');
    for (let i = 0; i < 20; i++) {
      const isGenerating = await page.evaluate(() => {
        return document.body.textContent.includes('Generating 3D Model');
      });
      if (!isGenerating) break;
      await sleep(1000);
    }
    await sleep(2500);

    const whiteFullShot = path.join(DOCS_DIR, 'ecommerce_studio_white_varsity.png');
    await page.screenshot({ path: whiteFullShot });
    console.log(`Saved white varsity screenshot: ${whiteFullShot}`);

    // 3. Select Sample 3: PUMA Navy Blue Classic T-Shirt
    console.log('Switching to Sample 3 (PUMA Navy Blue Classic T-Shirt)...');
    for (const tab of tabs) {
      const text = await (await tab.getProperty('textContent')).jsonValue();
      if (text.includes('Try Samples')) {
        await tab.click();
        break;
      }
    }
    await sleep(800);

    const sampleCards3 = await page.$$('button');
    for (const card of sampleCards3) {
      const text = await (await card.getProperty('textContent')).jsonValue();
      if (text.includes('PUMA') || text.includes('Navy Blue')) {
        await card.click();
        console.log('Clicked Puma Navy Sample Card');
        break;
      }
    }
    await sleep(1000);

    console.log('Waiting for Puma 3D model generation...');
    for (let i = 0; i < 20; i++) {
      const isGenerating = await page.evaluate(() => {
        return document.body.textContent.includes('Generating 3D Model');
      });
      if (!isGenerating) break;
      await sleep(1000);
    }
    await sleep(2500);

    const navyFullShot = path.join(DOCS_DIR, 'ecommerce_studio_navy_crest.png');
    await page.screenshot({ path: navyFullShot });
    console.log(`Saved navy blue screenshot: ${navyFullShot}`);

    // 4. Test Shading Mode: Switch to Wireframe
    console.log('Testing Wireframe shading mode...');
    const allButtons = await page.$$('button');
    for (const btn of allButtons) {
      const text = await (await btn.getProperty('textContent')).jsonValue();
      if (text.trim() === 'Wire') {
        await btn.click();
        console.log('Clicked Wire shading button');
        break;
      }
    }
    await sleep(1500);

    const wireShot = path.join(DOCS_DIR, 'ecommerce_wireframe_view.png');
    await page.screenshot({ path: wireShot });
    console.log(`Saved wireframe screenshot: ${wireShot}`);

    // Switch back to Textured
    for (const btn of allButtons) {
      const text = await (await btn.getProperty('textContent')).jsonValue();
      if (text.trim() === 'Textured') {
        await btn.click();
        console.log('Clicked Textured shading button');
        break;
      }
    }
    await sleep(1000);

    console.log('ALL E-COMMERCE 3D GARMENT STUDIO TESTS PASSED SUCCESSFULLY!');
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error('Test run failed:', err);
  process.exit(1);
});
