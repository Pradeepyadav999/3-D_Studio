"""Capture Size S views using Puppeteer to inspect the current Size S model."""
import subprocess
import json

# Launch puppeteer script specifically for Size S
puppeteer_script = """
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

async function selectSize(page, size) {
  return await page.evaluate((s) => {
    // Look for size button or row in table
    const buttons = Array.from(document.querySelectorAll('button, th, td'));
    const target = buttons.find(b => b.textContent && b.textContent.trim() === s);
    if (target) {
      target.click();
      return true;
    }
    return false;
  }, size);
}

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
    defaultViewport: { width: 1440, height: 900 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Click Size S in table header or buttons
    await page.evaluate(() => {
      const ths = Array.from(document.querySelectorAll('th, button'));
      const sEl = ths.find(el => el.textContent && el.textContent.trim() === 'S');
      if (sEl) sEl.click();
    });
    await new Promise(r => setTimeout(r, 500));

    await clickButtonWithText(page, 'Confirm Measurements');
    await new Promise(r => setTimeout(r, 500));
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
"""

with open("scripts/capture_size_s.js", "w") as f:
    f.write(puppeteer_script)

print("Saved scripts/capture_size_s.js")
