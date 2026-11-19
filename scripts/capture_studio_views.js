import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');

async function clickButtonWithText(page, text) {
  return await page.evaluate((t) => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent && b.textContent.includes(t));
    if (target) {
      target.click();
      return true;
    }
    return false;
  }, text);
}

async function run() {
  console.log('Capturing 5 canonical views of improved 3D Garment Studio model...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu-rasterization',
      '--window-size=1440,900',
      '--user-data-dir=/tmp/chrome-views-capture',
    ],
    defaultViewport: { width: 1440, height: 900 },
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Confirm measurements and generate 3D model
    console.log('Confirming measurements & generating 3D model...');
    await clickButtonWithText(page, 'Confirm Measurements');
    await new Promise(r => setTimeout(r, 500));
    await clickButtonWithText(page, 'Generate 3D Model');

    console.log('Waiting for Blender worker and Three.js viewport load...');
    await page.waitForFunction(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(b => b.textContent && b.textContent.includes('Download GLB'));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    await new Promise(r => setTimeout(r, 3000));

    // 1. Perspective View
    console.log('Capturing Perspective View...');
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 1200));
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_perspective.png') });
    console.log('Saved docs/view_perspective.png');

    // 2. Front View
    console.log('Capturing Front View...');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 1200));
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_front.png') });
    console.log('Saved docs/view_front.png');

    // 3. Back View
    console.log('Capturing Back View...');
    await clickButtonWithText(page, 'Back');
    await new Promise(r => setTimeout(r, 1200));
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_back.png') });
    console.log('Saved docs/view_back.png');

    // 4. Left View
    console.log('Capturing Left View...');
    await clickButtonWithText(page, 'Left');
    await new Promise(r => setTimeout(r, 1200));
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_left.png') });
    console.log('Saved docs/view_left.png');

    // 5. Right View
    console.log('Capturing Right View...');
    await clickButtonWithText(page, 'Right');
    await new Promise(r => setTimeout(r, 1200));
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_right.png') });
    console.log('Saved docs/view_right.png');

    // 6. Wireframe Overlay with Bounding Box
    console.log('Capturing Solid+Wire View with Bounding Box...');
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 800));
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 800));
    const boxBtn = await page.$('button[title*="Bounding Box"]');
    if (boxBtn) {
      await boxBtn.click();
      await new Promise(r => setTimeout(r, 800));
    }
    await page.screenshot({ path: path.join(DOCS_DIR, 'view_wireframe_bbox.png') });
    console.log('Saved docs/view_wireframe_bbox.png');

    console.log('All 5 canonical views + wireframe captured successfully!');

  } catch (err) {
    console.error('Capture Failure:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
