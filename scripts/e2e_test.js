import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');

async function clickButtonWithText(page, text) {
  const clicked = await page.evaluate((t) => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const target = buttons.find(b => b.textContent && b.textContent.includes(t));
    if (target) {
      target.click();
      return true;
    }
    return false;
  }, text);
  return clicked;
}

async function run() {
  console.log('Starting 3D Garment Studio End-to-End Automation Test...');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu-rasterization',
      '--window-size=1440,900',
      '--user-data-dir=/tmp/chrome-garment-e2e',
    ],
    defaultViewport: { width: 1440, height: 900 },
  });

  try {
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.error('PAGE ERROR:', err));

    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });

    // Wait for initial auto-loaded chart or load sample chart
    await new Promise(r => setTimeout(r, 2000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'step0_initial_studio.png') });
    console.log('Captured step0_initial_studio.png');

    // 1. Check if table is loaded; if not, click "Load Sample Chart"
    let tableExists = await page.$('table');
    if (!tableExists) {
      console.log('Clicking "Load Sample Chart"...');
      await clickButtonWithText(page, 'Load Sample Chart');
      await page.waitForSelector('table', { timeout: 15000 });
    }

    await new Promise(r => setTimeout(r, 1500));
    await page.screenshot({ path: path.join(DOCS_DIR, 'step1_extracted_table.png') });
    console.log('Captured step1_extracted_table.png');

    // 2. Click "Confirm Measurements"
    console.log('Confirming measurements...');
    await clickButtonWithText(page, 'Confirm Measurements');
    await new Promise(r => setTimeout(r, 800));

    // 3. Click "Generate 3D Model"
    console.log('Clicking "Generate 3D Model"...');
    const genClicked = await clickButtonWithText(page, 'Generate 3D Model');
    if (!genClicked) {
      throw new Error('Generate 3D Model button could not be clicked');
    }

    console.log('Generation started! Waiting for Blender worker to produce GLB and load in Three.js...');
    // Wait for Download GLB button to be enabled
    await page.waitForFunction(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(b => b.textContent && (b.textContent.includes('Download GLB') || b.textContent.includes('Export GLB')));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    console.log('3D GLB Model generated and loaded in viewport!');
    await new Promise(r => setTimeout(r, 3000)); // allow Three.js rendering

    await page.screenshot({ path: path.join(DOCS_DIR, 'step2_3d_model_solid.png') });
    console.log('Captured step2_3d_model_solid.png');

    // 4. Viewport controls: Switch view to Front, toggle Solid+Wire
    console.log('Testing Viewport View Controls (Front preset, Solid+Wire shading)...');
    await clickButtonWithText(page, 'Front');
    await new Promise(r => setTimeout(r, 1000));

    await clickButtonWithText(page, 'Solid+Wire');
    await new Promise(r => setTimeout(r, 1000));

    // Toggle Bounding Box Helper
    const boxBtn = await page.$('button[title*="Bounding Box"]');
    if (boxBtn) {
      await boxBtn.click();
      await new Promise(r => setTimeout(r, 1000));
    }

    await page.screenshot({ path: path.join(DOCS_DIR, 'step3_3d_model_wireframe_bbox.png') });
    console.log('Captured step3_3d_model_wireframe_bbox.png');

    // 5. Test Live Parameter Update & Model Regeneration
    console.log('Testing Live Measurement Parameter Update & Model Regeneration...');
    // Focus the chest number input in the right panel and type 114
    await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input[type="number"]'));
      // The right panel inputs have values 107, 46, 71, 20
      const chestInp = inputs.find(i => i.value === '107' || i.value === '107.0');
      if (chestInp) {
        chestInp.focus();
      }
    });

    await page.keyboard.press('Backspace');
    await page.keyboard.press('Backspace');
    await page.keyboard.press('Backspace');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('114');

    await new Promise(r => setTimeout(r, 1000));
    console.log('Clicking "Regenerate Model"...');
    await clickButtonWithText(page, 'Regenerate Model');

    // Wait for regeneration
    await page.waitForFunction(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(b => b.textContent && b.textContent.includes('Download GLB'));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: path.join(DOCS_DIR, 'step4_regenerated_model.png') });
    console.log('Captured step4_regenerated_model.png');

    // 6. Test Size Matrix Modal
    console.log('Opening Size Matrix Modal...');
    await clickButtonWithText(page, 'Size Matrix');
    await new Promise(r => setTimeout(r, 1200));

    await page.screenshot({ path: path.join(DOCS_DIR, 'step5_size_matrix_modal.png') });
    console.log('Captured step5_size_matrix_modal.png');

    console.log('All End-to-End automation tests completed successfully!');

  } catch (err) {
    console.error('E2E Test Failure:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
