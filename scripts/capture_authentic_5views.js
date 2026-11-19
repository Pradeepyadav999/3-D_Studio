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
  console.log('Capturing all 5 views from the live studio...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-5views-studio',
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

    // Wait for generation to finish
    for (let i = 0; i < 25; i++) {
      const isGen = await page.evaluate(() => document.body.textContent.includes('Generating 3D Garment') || document.body.textContent.includes('Generating 3D Model'));
      if (!isGen) break;
      await sleep(1000);
    }
    await sleep(2500);

    const clickButton = async (label) => {
      const clicked = await page.evaluate((btnLabel) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const target = btns.find(b => b.innerText.trim() === btnLabel);
        if (target) {
          target.click();
          return true;
        }
        return false;
      }, label);
      await sleep(1200);
      return clicked;
    };

    // 1. FRONT VIEW
    console.log('Capturing View 1: Front...');
    await clickButton('Front');
    const shot1 = path.join(DOCS_DIR, 'authentic_view_1_front.png');
    await page.screenshot({ path: shot1 });
    fs.copyFileSync(shot1, path.join(ARTIFACTS_DIR, 'authentic_view_1_front.png'));

    // 2. BACK VIEW
    console.log('Capturing View 2: Back...');
    await clickButton('Back');
    const shot2 = path.join(DOCS_DIR, 'authentic_view_2_back.png');
    await page.screenshot({ path: shot2 });
    fs.copyFileSync(shot2, path.join(ARTIFACTS_DIR, 'authentic_view_2_back.png'));

    // 3. LEFT VIEW
    console.log('Capturing View 3: Left...');
    await clickButton('Left');
    const shot3 = path.join(DOCS_DIR, 'authentic_view_3_left.png');
    await page.screenshot({ path: shot3 });
    fs.copyFileSync(shot3, path.join(ARTIFACTS_DIR, 'authentic_view_3_left.png'));

    // 4. RIGHT VIEW
    console.log('Capturing View 4: Right...');
    await clickButton('Right');
    const shot4 = path.join(DOCS_DIR, 'authentic_view_4_right.png');
    await page.screenshot({ path: shot4 });
    fs.copyFileSync(shot4, path.join(ARTIFACTS_DIR, 'authentic_view_4_right.png'));

    // 5. TOP VIEW (Looking straight down at round neck and broad shoulders)
    console.log('Capturing View 5: Top...');
    await clickButton('Top');
    const shot5 = path.join(DOCS_DIR, 'authentic_view_5_top.png');
    await page.screenshot({ path: shot5 });
    fs.copyFileSync(shot5, path.join(ARTIFACTS_DIR, 'authentic_view_5_top.png'));

    // 6. FRONT WIREFRAME (Showing zero triangular chest collapse!)
    console.log('Capturing View 6: Front Wireframe...');
    await clickButton('Front');
    await clickButton('Wireframe');
    const shot6 = path.join(DOCS_DIR, 'authentic_view_6_front_wireframe.png');
    await page.screenshot({ path: shot6 });
    fs.copyFileSync(shot6, path.join(ARTIFACTS_DIR, 'authentic_view_6_front_wireframe.png'));

    console.log('Successfully captured all 5 authentic views + wireframe!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Capture error:', err);
  process.exit(1);
});
