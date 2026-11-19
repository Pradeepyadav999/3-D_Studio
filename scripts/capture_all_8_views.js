import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');

async function clickButtonWithText(page, text) {
  return await page.evaluate((t) => {
    const buttons = Array.from(document.querySelectorAll('button, div, span, th'));
    const target = buttons.find(b => b.textContent && b.textContent.trim() === t);
    if (target) {
      target.click();
      return true;
    }
    return false;
  }, text);
}

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900', '--user-data-dir=/tmp/chrome-8views-v3'],
    defaultViewport: { width: 1440, height: 900 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Select Size S
    await page.evaluate(() => {
      const ths = Array.from(document.querySelectorAll('th, button, td'));
      const sEl = ths.find(el => el.textContent && el.textContent.trim() === 'S');
      if (sEl) sEl.click();
    });
    await new Promise(r => setTimeout(r, 600));

    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const conf = btns.find(b => b.textContent && b.textContent.includes('Confirm Measurements'));
      if (conf) conf.click();
    });
    await new Promise(r => setTimeout(r, 600));

    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const gen = btns.find(b => b.textContent && b.textContent.includes('Generate 3D Model'));
      if (gen) gen.click();
    });

    console.log('Waiting for model generation...');
    await page.waitForFunction(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(b => b.textContent && b.textContent.includes('Download GLB'));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    await new Promise(r => setTimeout(r, 2500));

    const canvasBox = await page.evaluate(() => {
      const canvas = document.querySelector('canvas');
      if (!canvas) return null;
      const rect = canvas.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    });

    const cx = canvasBox ? canvasBox.x + canvasBox.width / 2 : 720;
    const cy = canvasBox ? canvasBox.y + canvasBox.height / 2 : 450;

    // 1. Front solid view
    console.log('Capturing View 1: Front solid view');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 600));
    await clickButtonWithText(page, 'Solid');
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_front_solid.png') });

    // 2. Front wireframe view
    console.log('Capturing View 2: Front wireframe view');
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_front_wireframe.png') });

    // 3. Back view
    console.log('Capturing View 3: Back view');
    await clickButtonWithText(page, 'Solid');
    await new Promise(r => setTimeout(r, 400));
    await clickButtonWithText(page, 'Back');
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_back.png') });

    // 4. Side view
    console.log('Capturing View 4: Side view');
    await clickButtonWithText(page, 'Left');
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_side.png') });

    // 5. Perspective view
    console.log('Capturing View 5: Perspective view');
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_perspective.png') });

    // 6. Close-up of Left Shoulder (wearer's left = screen right)
    console.log('Capturing View 6: Close-up of Left Shoulder');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 400));
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 400));
    await page.evaluate(() => {
      if (window.__setViewportCamera) {
        window.__setViewportCamera(-0.14, 0.24, 0.45, -0.14, 0.24, 0);
      }
    });
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_left_shoulder_closeup.png') });

    // 7. Close-up of Right Shoulder (wearer's right = screen left)
    console.log('Capturing View 7: Close-up of Right Shoulder');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 400));
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 400));
    await page.evaluate(() => {
      if (window.__setViewportCamera) {
        window.__setViewportCamera(0.14, 0.24, 0.45, 0.14, 0.24, 0);
      }
    });
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_right_shoulder_closeup.png') });

    // 8. Close-up of Neckline and Collar
    console.log('Capturing View 8: Close-up of Neckline and Collar');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 400));
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 400));
    await page.evaluate(() => {
      if (window.__setViewportCamera) {
        window.__setViewportCamera(0.0, 0.34, 0.45, 0.0, 0.24, 0.0);
      }
    });
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(DOCS_DIR, 'v3_neckline_collar_closeup.png') });

    console.log('All 8 views captured successfully!');
  } finally {
    await browser.close();
  }
}
run();
