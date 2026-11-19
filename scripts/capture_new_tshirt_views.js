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
  console.log('Testing new T-shirt model in browser viewport...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1000',
      '--user-data-dir=/tmp/chrome-tshirt-verify',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1000 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(2500);

    // Click "Try Samples" -> Roadster Black to trigger the new generator once updated
    console.log('Taking full studio screenshot...');
    await page.screenshot({ path: path.join(DOCS_DIR, 'new_tshirt_studio_initial.png') });

  } finally {
    await browser.close();
  }
}

run().catch(console.error);
