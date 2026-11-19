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
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900', '--user-data-dir=/tmp/chrome-size-s'],
    defaultViewport: { width: 1440, height: 900 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Click Size S in table header or buttons
    const clickedS = await page.evaluate(() => {
      const ths = Array.from(document.querySelectorAll('th, button, div'));
      const sEl = ths.find(el => el.textContent && el.textContent.trim() === 'S');
      if (sEl) {
        sEl.click();
        return true;
      }
      return false;
    });
    console.log('Clicked Size S:', clickedS);
    await new Promise(r => setTimeout(r, 800));

    await clickButtonWithText(page, 'Confirm Measurements');
    await new Promise(r => setTimeout(r, 800));
    await clickButtonWithText(page, 'Generate 3D Model');

    await page.waitForFunction(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(b => b.textContent && b.textContent.includes('Download GLB'));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    await new Promise(r => setTimeout(r, 2500));

    // Capture Front, Persp, Back, Left, Right for Size S
    await clickButtonWithText(page, 'Persp');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_persp.png') });

    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_front.png') });

    await clickButtonWithText(page, 'Back');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_back.png') });

    await clickButtonWithText(page, 'Left');
    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'size_s_left.png') });

    console.log('Size S screenshots captured!');
  } finally {
    await browser.close();
  }
}
run();
