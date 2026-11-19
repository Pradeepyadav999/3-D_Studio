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
  console.log('Verifying Flipkart Size Chart Parameters in Studio...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-param-verify',
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

    // Wait for generation
    for (let i = 0; i < 25; i++) {
      const isGen = await page.evaluate(() => document.body.textContent.includes('Generating 3D Model') || document.body.textContent.includes('Generating 3D Garment'));
      if (!isGen) break;
      await sleep(1000);
    }
    await sleep(2500);

    // Inspect presence of Chest, Shoulder, Length inputs
    const paramInputs = await page.evaluate(() => {
      const labels = Array.from(document.querySelectorAll('label')).map(l => l.innerText.trim());
      const inputs = Array.from(document.querySelectorAll('input[type="number"]')).map(inp => ({
        placeholder: inp.placeholder,
        value: inp.value
      }));
      return { labels, inputs };
    });
    console.log('Detected parameter controls:', paramInputs);

    // Screenshot 1: Default Flipkart Size Parameters (Chest 106, Shoulder 49, Length 71)
    const shot1 = path.join(DOCS_DIR, 'flipkart_parameters_studio.png');
    await page.screenshot({ path: shot1 });
    fs.copyFileSync(shot1, path.join(ARTIFACTS_DIR, 'flipkart_parameters_studio.png'));
    console.log(`Saved screenshot: ${shot1}`);

    // Click INCH unit toggle
    console.log('Switching to INCH unit toggle...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const inchBtn = btns.find(b => b.innerText.trim() === 'INCH');
      if (inchBtn) inchBtn.click();
    });
    await sleep(1500);

    // Screenshot 2: INCH view
    const shot2 = path.join(DOCS_DIR, 'flipkart_parameters_inches.png');
    await page.screenshot({ path: shot2 });
    fs.copyFileSync(shot2, path.join(ARTIFACTS_DIR, 'flipkart_parameters_inches.png'));
    console.log(`Saved screenshot: ${shot2}`);

    console.log('Flipkart parameters verification completed successfully!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Error during verification:', err);
  process.exit(1);
});
