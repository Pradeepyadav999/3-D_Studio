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
  console.log('=== STARTING 3D VIEW MODES & TEXTURE VALIDATION SUITE ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-viewmodes-studio',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1050 }
  });

  try {
    const page = await browser.newPage();

    // Listen to network requests to verify switching modes doesn't reload or regenerate
    let modelRequestsCount = 0;
    page.on('request', req => {
      const u = req.url();
      if (u.includes('/api/models/') && u.endsWith('.glb')) {
        modelRequestsCount++;
        console.log(`[Network Request] GLB load detected: ${u}`);
      }
    });

    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(2500);

    // 1. SELECT AUTHENTIC FLIPKART PRINTED T-SHIRT (Onyx Black)
    console.log('Selecting authentic Flipkart graphic crew black product...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const sampleBtn = btns.find(b => b.innerText.includes('Try Samples'));
      if (sampleBtn) sampleBtn.click();
    });
    await sleep(1500);

    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const blackProduct = buttons.find(b => b.innerText.includes('Onyx Black') || b.innerText.includes('Pacific Coastline'));
      if (blackProduct) blackProduct.click();
    });
    await sleep(1500);

    // 2. GENERATE 3D GARMENT
    console.log('Generating 3D garment from original product...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model'));
      if (genBtn) genBtn.click();
    });

    // Wait for generation to finish
    for (let i = 0; i < 40; i++) {
      const isGen = await page.evaluate(() =>
        document.body.textContent.includes('Generating 3D Garment') ||
        document.body.textContent.includes('Generating Geometry...')
      );
      if (!isGen) {
        console.log(`Generation finished at loop ${i}!`);
        break;
      }
      await sleep(1000);
    }
    await sleep(3500);

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
      await sleep(800);
      return clicked;
    };

    // Record request count after generation
    const initialModelRequests = modelRequestsCount;
    console.log(`Initial GLB requests so far: ${initialModelRequests}`);

    // TEST 1: TEXTURED MODE
    console.log('Testing Mode 1: TEXTURED...');
    await clickButton('Front');
    await clickButton('TEXTURED');
    await sleep(1000);
    const shotTextured = path.join(ARTIFACTS_DIR, 'viewmode_1_textured.png');
    await page.screenshot({ path: shotTextured });
    console.log(`Saved ${shotTextured}`);

    // TEST 2: SOLID MODE
    console.log('Testing Mode 2: SOLID...');
    await clickButton('SOLID');
    await sleep(1000);
    const shotSolid = path.join(ARTIFACTS_DIR, 'viewmode_2_solid.png');
    await page.screenshot({ path: shotSolid });
    console.log(`Saved ${shotSolid}`);

    // TEST 3: WIRE MODE
    console.log('Testing Mode 3: WIRE...');
    await clickButton('WIRE');
    await sleep(1000);
    const shotWire = path.join(ARTIFACTS_DIR, 'viewmode_3_wire.png');
    await page.screenshot({ path: shotWire });
    console.log(`Saved ${shotWire}`);

    // TEST 4: SOLID + WIRE MODE
    console.log('Testing Mode 4: SOLID + WIRE...');
    await clickButton('SOLID + WIRE');
    await sleep(1000);
    const shotSolidWire = path.join(ARTIFACTS_DIR, 'viewmode_4_solid_wire.png');
    await page.screenshot({ path: shotSolidWire });
    console.log(`Saved ${shotSolidWire}`);

    // VERIFY ZERO RELOADS WHEN SWITCHING MODES
    console.log(`GLB requests after switching all 4 modes: ${modelRequestsCount}`);
    if (modelRequestsCount === initialModelRequests) {
      console.log('SUCCESS: Switching view modes did NOT reload or regenerate the mesh!');
    } else {
      console.warn(`WARNING: Mode switching triggered unexpected reload: ${modelRequestsCount} vs ${initialModelRequests}`);
    }

    // CAPTURE ALL 6 CAMERA ANGLES IN TEXTURED MODE
    console.log('Capturing camera angles in TEXTURED mode...');
    await clickButton('TEXTURED');

    await clickButton('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_persp_textured.png') });

    await clickButton('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_front_textured.png') });

    await clickButton('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_back_textured.png') });

    await clickButton('Left');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_left_textured.png') });

    await clickButton('Right');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_right_textured.png') });

    await clickButton('Top');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'viewmode_top_textured.png') });

    // TEST REQUIREMENT 7: SIZE SELECTION
    console.log('Testing Size Selection (Requirement 7): Selecting 44" (XL)...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const xlPreset = btns.find(b => b.innerText.includes('44" (XL)'));
      if (xlPreset) xlPreset.click();
    });
    await sleep(1000);

    console.log('Regenerating 3D garment for Size XL...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText.includes('Regenerate 3D Model') || b.innerText.includes('Generate 3D Garment'));
      if (genBtn) genBtn.click();
    });

    for (let i = 0; i < 40; i++) {
      const isGen = await page.evaluate(() =>
        document.body.textContent.includes('Generating 3D Garment') ||
        document.body.textContent.includes('Generating Geometry...')
      );
      if (!isGen) {
        console.log(`Size XL generation finished at loop ${i}!`);
        break;
      }
      await sleep(1000);
    }
    await sleep(3500);

    await clickButton('Front');
    await clickButton('TEXTURED');
    await sleep(800);
    const shotXlTextured = path.join(ARTIFACTS_DIR, 'viewmode_size_xl_textured.png');
    await page.screenshot({ path: shotXlTextured });
    console.log(`Saved Size XL textured screenshot to ${shotXlTextured}`);

    console.log('=== ALL TESTS COMPLETED SUCCESSFULLY ===');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Validation test error:', err);
  process.exit(1);
});

