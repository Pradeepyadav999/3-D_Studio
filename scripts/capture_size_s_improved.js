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
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900', '--user-data-dir=/tmp/chrome-size-s-imp'],
    defaultViewport: { width: 1440, height: 900 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Select Size S in table header
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

    // 1. Perspective View
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_persp_improved.png') });
    console.log('Captured Persp');

    // 2. Front View
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_front_improved.png') });
    console.log('Captured Front');

    // 3. Back View
    await clickButtonWithText(page, 'Back');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_back_improved.png') });
    console.log('Captured Back');

    // 4. Left View
    await clickButtonWithText(page, 'Left');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_left_improved.png') });
    console.log('Captured Left');

    // 5. Right View
    await clickButtonWithText(page, 'Right');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_right_improved.png') });
    console.log('Captured Right');

    // 6. Solid+Wire View
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 600));
    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 600));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_wireframe_improved.png') });
    console.log('Captured Wireframe');

  } finally {
    await browser.close();
  }
}
run();
