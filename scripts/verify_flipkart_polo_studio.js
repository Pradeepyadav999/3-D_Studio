import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const ARTIFACTS_DIR = '/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images';

try { fs.mkdirSync(ARTIFACTS_DIR, { recursive: true }); } catch (e) {}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('=== STARTING FLIPKART POLO END-TO-END VERIFICATION SUITE ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-polo-studio',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1050 }
  });

  try {
    const page = await browser.newPage();

    let modelRequestsCount = 0;
    page.on('request', req => {
      const u = req.url();
      if (u.includes('/api/models/') && u.endsWith('.glb')) {
        modelRequestsCount++;
        console.log(`[Network Request] GLB load: ${u}`);
      }
    });

    console.log('1. Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await sleep(2500);

    // 2. ANALYZE FLIPKART URL
    console.log('2. Entering Flipkart URL: https://dl.flipkart.com/s/Oclx04NNNN ...');
    const inputSelector = 'input[placeholder*="flipkart.com"]';
    await page.waitForSelector(inputSelector);
    await page.type(inputSelector, 'https://dl.flipkart.com/s/Oclx04NNNN');
    await sleep(500);

    console.log('   Clicking "Analyze Product & Extract Design"...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const analyzeBtn = btns.find(b => b.innerText.includes('Analyze Product') || b.innerText.includes('Extract Design'));
      if (analyzeBtn) analyzeBtn.click();
    });

    // Wait for analysis to complete
    console.log('   Waiting for product analysis to complete...');
    for (let i = 0; i < 30; i++) {
      const isAnalyzing = await page.evaluate(() =>
        document.body.textContent.includes('Extracting & Analyzing') ||
        document.body.textContent.includes('Analyzing Product...')
      );
      if (!isAnalyzing) {
        console.log(`   Analysis complete at loop ${i}!`);
        break;
      }
      await sleep(1000);
    }
    await sleep(2500);

    // Verify product title displayed
    const productTitle = await page.evaluate(() => {
      const el = document.querySelector('h3, .font-medium');
      return document.body.textContent.includes('Allen Solly') ? 'Allen Solly Polo Detected' : 'Not detected';
    });
    console.log(`   Product Title check: ${productTitle}`);

    // 3. GENERATE 3D GARMENT
    console.log('3. Clicking "Generate 3D Garment"...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const genBtn = btns.find(b => b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model'));
      if (genBtn) genBtn.click();
    });

    console.log('   Waiting for Blender 3D generation...');
    for (let i = 0; i < 40; i++) {
      const isGenerating = await page.evaluate(() =>
        document.body.textContent.includes('Generating 3D Garment') ||
        document.body.textContent.includes('Generating Geometry...')
      );
      if (!isGenerating) {
        console.log(`   Generation finished at loop ${i}!`);
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

    // 4. CAPTURE ALL 4 VIEW MODES
    console.log('4. Capturing View Modes...');

    // A. TEXTURED MODE (Front view)
    console.log('   Mode 1: TEXTURED (Front Camera)...');
    await clickButton('Front');
    await clickButton('TEXTURED');
    await sleep(1200);
    const shotPoloTextured = path.join(ARTIFACTS_DIR, 'polo_mode_1_textured.png');
    await page.screenshot({ path: shotPoloTextured });
    console.log(`   Saved ${shotPoloTextured}`);

    // B. SOLID MODE
    console.log('   Mode 2: SOLID (Front Camera)...');
    await clickButton('SOLID');
    await sleep(1200);
    const shotPoloSolid = path.join(ARTIFACTS_DIR, 'polo_mode_2_solid.png');
    await page.screenshot({ path: shotPoloSolid });
    console.log(`   Saved ${shotPoloSolid}`);

    // C. WIRE MODE
    console.log('   Mode 3: WIRE (Front Camera)...');
    await clickButton('WIRE');
    await sleep(1200);
    const shotPoloWire = path.join(ARTIFACTS_DIR, 'polo_mode_3_wire.png');
    await page.screenshot({ path: shotPoloWire });
    console.log(`   Saved ${shotPoloWire}`);

    // D. SOLID + WIRE MODE
    console.log('   Mode 4: SOLID + WIRE (Front Camera)...');
    await clickButton('SOLID + WIRE');
    await sleep(1200);
    const shotPoloSolidWire = path.join(ARTIFACTS_DIR, 'polo_mode_4_solid_wire.png');
    await page.screenshot({ path: shotPoloSolidWire });
    console.log(`   Saved ${shotPoloSolidWire}`);

    // 5. CAPTURE ALL 6 CAMERA ANGLES IN TEXTURED MODE
    console.log('5. Capturing Camera Angles in TEXTURED mode...');
    await clickButton('TEXTURED');

    console.log('   Angle: Perspective...');
    await clickButton('Perspective');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_persp_textured.png') });

    console.log('   Angle: Front...');
    await clickButton('Front');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_front_textured.png') });

    console.log('   Angle: Back...');
    await clickButton('Back');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_back_textured.png') });

    console.log('   Angle: Left...');
    await clickButton('Left');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_left_textured.png') });

    console.log('   Angle: Right...');
    await clickButton('Right');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_right_textured.png') });

    console.log('   Angle: Top...');
    await clickButton('Top');
    await sleep(1000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'polo_top_textured.png') });

    console.log('=== ALL FLIPKART POLO VALIDATIONS AND SCREENSHOTS COMPLETED! ===');
  } catch (err) {
    console.error('Test error:', err);
  } finally {
    await browser.close();
  }
}

run();
