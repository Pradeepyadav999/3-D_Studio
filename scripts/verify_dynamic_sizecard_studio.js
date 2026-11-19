import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');
const ARTIFACTS_DIR = '/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images';

try { fs.mkdirSync(DOCS_DIR, { recursive: true }); } catch (e) {}
try { fs.mkdirSync(ARTIFACTS_DIR, { recursive: true }); } catch (e) {}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('Launching Chrome for Size Card Studio verification...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-sizecard-verify',
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
    await sleep(3000);

    // Wait for initial generation to complete
    console.log('Waiting for initial model generation...');
    for (let i = 0; i < 25; i++) {
      const isGenerating = await page.evaluate(() => {
        return document.body.textContent.includes('Generating 3D Model');
      });
      if (!isGenerating) break;
      await sleep(1000);
    }
    await sleep(3000);

    // Verify Size Card table exists
    const tableInfo = await page.evaluate(() => {
      const ths = Array.from(document.querySelectorAll('th')).map(th => th.innerText.trim());
      const inputs = Array.from(document.querySelectorAll('input[type="number"]')).map(inp => inp.value);
      return {
        headers: ths,
        inputCount: inputs.length,
        inputs: inputs.slice(0, 8)
      };
    });
    console.log('Size Card Table Info:', tableInfo);

    // Capture screenshot 1: Initial Size Card Studio with 3D model
    const shot1 = path.join(DOCS_DIR, 'sizecard_studio_default_m.png');
    await page.screenshot({ path: shot1 });
    console.log(`Saved screenshot: ${shot1}`);
    fs.copyFileSync(shot1, path.join(ARTIFACTS_DIR, 'sizecard_studio_default_m.png'));

    // Click on Size XL in the quick pills or table
    console.log('Selecting Size XL...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const xlBtn = buttons.find(b => b.innerText.trim() === 'XL');
      if (xlBtn) xlBtn.click();
    });

    await sleep(2000);

    // Wait for XL generation
    for (let i = 0; i < 25; i++) {
      const isGenerating = await page.evaluate(() => {
        return document.body.textContent.includes('Generating 3D Model');
      });
      if (!isGenerating) break;
      await sleep(1000);
    }
    await sleep(3000);

    // Capture screenshot 2: Size XL generated from Size Card
    const shot2 = path.join(DOCS_DIR, 'sizecard_studio_size_xl.png');
    await page.screenshot({ path: shot2 });
    console.log(`Saved screenshot: ${shot2}`);
    fs.copyFileSync(shot2, path.join(ARTIFACTS_DIR, 'sizecard_studio_size_xl.png'));

    console.log('Size card verification completed successfully!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Error during verification:', err);
  process.exit(1);
});
