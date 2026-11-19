import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const ARTIFACTS_DIR = '/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images';

try { fs.mkdirSync(ARTIFACTS_DIR, { recursive: true }); } catch (e) { }

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('=== STARTING FINAL VERIFICATION: NORMAL VS VALIDATION MODES (ALL 6 VIEWS) ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-modes-audit-v3',
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
    await sleep(2500);

    // Click "Try Samples"
    console.log('Opening sample catalog...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const sampleBtn = btns.find(b => b.innerText && b.innerText.includes('Try Samples'));
      if (sampleBtn) sampleBtn.click();
    });
    await sleep(1500);

    // Select Graphic Crew Black product
    console.log('Selecting Onyx Black graphic crew neck...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const blackProduct = buttons.find(b => b.innerText && (b.innerText.includes('Onyx Black') || b.innerText.includes('Pacific Coastline') || b.innerText.includes('Black')));
      if (blackProduct) blackProduct.click();
    });
    await sleep(1500);

    // Click Generate 3D Garment
    console.log('Generating 3D Garment...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && (b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model')));
      if (genBtn) genBtn.click();
    });

    // Wait for generation
    for (let i = 0; i < 40; i++) {
      const isGen = await page.evaluate(() =>
        document.body.textContent.includes('Generating 3D Garment') ||
        document.body.textContent.includes('Generating Geometry...') ||
        document.body.textContent.includes('Lofting Torso')
      );
      if (!isGen) {
        console.log(`Generation completed at loop ${i}!`);
        break;
      }
      await sleep(1000);
    }
    await sleep(4000);

    const clickButton = async (label) => {
      const clicked = await page.evaluate((btnLabel) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const target = btns.find(b => b.innerText && b.innerText.trim().toUpperCase() === btnLabel.toUpperCase());
        if (target) {
          target.click();
          return true;
        }
        return false;
      }, label);
      await sleep(900);
      return clicked;
    };

    const toggleValidation = async () => {
      await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const valBtn = btns.find(b => b.innerText && b.innerText.includes('VALIDATION'));
        if (valBtn) valBtn.click();
      });
      await sleep(900);
    };

    const cameraViews = ['Front', 'Back', 'Left', 'Right', 'Top', 'Perspective'];

    for (const view of cameraViews) {
      console.log(`\n--- Testing Camera Preset: ${view} ---`);
      
      // Set Camera Preset
      await clickButton(view);
      await sleep(600);

      // 1. Normal Mode Screenshot (Clean Hero T-shirt)
      const normalFile = `view_${view.toLowerCase()}_normal.png`;
      console.log(`Capturing ${view} in Normal Mode -> ${normalFile}`);
      await page.screenshot({ path: path.join(ARTIFACTS_DIR, normalFile) });

      // 2. Toggle to Validation Mode
      await toggleValidation();
      await sleep(600);

      // 3. Validation Mode Screenshot (Calibrated Grid & 3D Overlays)
      const valFile = `view_${view.toLowerCase()}_validation.png`;
      console.log(`Capturing ${view} in Validation Mode -> ${valFile}`);
      await page.screenshot({ path: path.join(ARTIFACTS_DIR, valFile) });

      // 4. Toggle back to Normal Mode
      await toggleValidation();
      await sleep(400);
    }

    // Capture Accuracy Report Modal
    console.log('\n--- Capturing Measurement Accuracy Audit Modal ---');
    await clickButton('ACCURACY');
    await sleep(1500);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'accuracy_audit_modal_pass.png') });

    // Close Modal
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const closeBtn = btns.find(b => b.innerText && (b.innerText.includes('Close') || b.innerText.includes('✕')));
      if (closeBtn) closeBtn.click();
    });
    await sleep(1000);

    // Test Multi-Size: Switch to Size XL
    console.log('\n--- Testing Multi-Size: Size XL ---');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const xlBtn = btns.find(b => b.innerText && b.innerText.trim() === 'XL');
      if (xlBtn) xlBtn.click();
    });
    await sleep(1000);

    // Regenerate for XL
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && (b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model')));
      if (genBtn) genBtn.click();
    });

    for (let i = 0; i < 40; i++) {
      const isGen = await page.evaluate(() =>
        document.body.textContent.includes('Generating 3D Garment') ||
        document.body.textContent.includes('Generating Geometry...') ||
        document.body.textContent.includes('Lofting Torso')
      );
      if (!isGen) {
        console.log(`XL Generation completed at loop ${i}!`);
        break;
      }
      await sleep(1000);
    }
    await sleep(3500);

    // Capture XL Front View in Normal Mode
    await clickButton('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'size_xl_front_normal.png') });

    // Capture XL Front View in Validation Mode
    await toggleValidation();
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'size_xl_front_validation.png') });

    console.log('=== ALL 14 VERIFICATION SCREENSHOTS CAPTURED SUCCESSFULLY ===');
  } catch (err) {
    console.error('Error during verification:', err);
  } finally {
    await browser.close();
  }
}

run();
