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
  console.log('=== STARTING 3D GARMENT GEOMETRY & CALIBRATED VIEWPORT VERIFICATION ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-garment-audit-v2',
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
    console.log('Generating 3D Garment with Blender BMesh Engine...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText && (b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model')));
      if (genBtn) genBtn.click();
    });

    // Wait for generation to complete
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
      await sleep(1000);
      return clicked;
    };

    // 1. Front View with 3D Dimension Overlays & Calibrated Metric Grid
    console.log('1. Capturing Front View with Dimensions & Calibrated Metric Grid...');
    await clickButton('Front');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_view_front_dimensions.png') });

    // 2. Perspective View with 10x10x10cm Reference Cube & Dimensions
    console.log('2. Capturing Perspective View with Dimensions...');
    await clickButton('Perspective');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_view_perspective_dimensions.png') });

    // 3. Solid Mode (Inspection of natural shoulders, relaxed crew neck, symmetric tubular sleeves)
    console.log('3. Capturing Solid Mode...');
    await clickButton('SOLID');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_mode_solid.png') });

    // 4. Wire Mode (Inspection of 2-manifold polygonal topology & mesh density)
    console.log('4. Capturing Wire Mode...');
    await clickButton('WIRE');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_mode_wire.png') });

    // 5. Solid + Wire Mode
    console.log('5. Capturing Solid + Wire Mode...');
    await clickButton('SOLID + WIRE');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_mode_solid_wire.png') });

    // Switch back to Textured
    await clickButton('TEXTURED');

    // 6. Left Side View (Torso Depth & Sleeve Drape)
    console.log('6. Capturing Left Side View...');
    await clickButton('Left');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_view_side_left.png') });

    // 7. Top View (Neckline Opening & Shoulder Span)
    console.log('7. Capturing Top View...');
    await clickButton('Top');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_view_top.png') });

    // 8. Back View (Back Neckline & Upper Back Proportions)
    console.log('8. Capturing Back View...');
    await clickButton('Back');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_view_back.png') });

    // 9. Measurement Accuracy Audit Modal (Pass/Fail table)
    console.log('9. Opening Measurement Accuracy Audit Modal...');
    await clickButton('ACCURACY');
    await sleep(1500);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'audit_accuracy_report_modal.png') });

    console.log('=== ALL AUDIT VERIFICATION SCREENSHOTS CAPTURED SUCCESSFULLY ===');
  } catch (err) {
    console.error('Error during verification:', err);
  } finally {
    await browser.close();
  }
}

run();
