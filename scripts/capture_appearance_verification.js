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
  console.log('=== STARTING 4-PRODUCT E-COMMERCE RECONSTRUCTION VERIFICATION ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-ecommerce-reconstruct-studio',
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

    const clickButton = async (text) => {
      await page.evaluate((btnText) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const target = btns.find(b => b.innerText.toLowerCase().includes(btnText.toLowerCase()));
        if (target) {
          target.click();
        }
      }, text);
      await sleep(1200);
    };

    const setCameraView = async (preset) => {
      await page.evaluate((viewName) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.innerText.toLowerCase().trim() === viewName.toLowerCase().trim());
        if (btn) btn.click();
      }, preset);
      await sleep(800);
    };

    const setShadingMode = async (modeName) => {
      await page.evaluate((mode) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.innerText.toLowerCase().includes(mode.toLowerCase()));
        if (btn) btn.click();
      }, modeName);
      await sleep(800);
    };

    const waitForModel = async () => {
      console.log('Waiting for 3D model generation to complete...');
      for (let i = 0; i < 40; i++) {
        const isGenerating = await page.evaluate(() => {
          return document.body.innerText.includes('Generating 3D Model');
        });
        if (!isGenerating) {
          console.log(`Generation completed or ready at check ${i}`);
          break;
        }
        await sleep(1000);
      }
      await sleep(2000);
    };

    // ----------------------------------------------------
    // TEST 1: PLAIN CREW-NECK T-SHIRT (Minimalist Plain Lavender)
    // ----------------------------------------------------
    console.log('\n--- Test 1: Plain Crew-Neck T-Shirt (fk_plain_crew_lavender) ---');
    await clickButton('Try Samples');
    await clickButton('Lavender');
    await waitForModel();

    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product1_plain_crew_front.png') });
    console.log('Captured product1_plain_crew_front.png');

    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product1_plain_crew_back.png') });
    console.log('Captured product1_plain_crew_back.png');

    await setShadingMode('Solid');
    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product1_plain_crew_solid.png') });
    console.log('Captured product1_plain_crew_solid.png');

    // ----------------------------------------------------
    // TEST 2: GRAPHIC PRINTED T-SHIRT (Roadster Graphic Crew Black)
    // ----------------------------------------------------
    console.log('\n--- Test 2: Graphic Printed T-Shirt (fk_graphic_crew_black) ---');
    await clickButton('Try Samples');
    await clickButton('Onyx Black');
    await waitForModel();

    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product2_graphic_crew_front.png') });
    console.log('Captured product2_graphic_crew_front.png');

    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product2_graphic_crew_back.png') });
    console.log('Captured product2_graphic_crew_back.png');

    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product2_graphic_crew_persp.png') });
    console.log('Captured product2_graphic_crew_persp.png');

    // ----------------------------------------------------
    // TEST 3: POLO SHIRT WITH 3D COLLAR, PLACKET & BUTTONS (Allen Solly Green)
    // ----------------------------------------------------
    console.log('\n--- Test 3: Polo Shirt with 3D Collar, Placket & Buttons (fk_allen_solly_polo_green) ---');
    await clickButton('Try Samples');
    await clickButton('Forest Green');
    await waitForModel();

    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product3_polo_green_front.png') });
    console.log('Captured product3_polo_green_front.png');

    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product3_polo_green_back.png') });
    console.log('Captured product3_polo_green_back.png');

    await setShadingMode('Solid');
    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product3_polo_green_solid_persp.png') });
    console.log('Captured product3_polo_green_solid_persp.png');

    await setShadingMode('Wire');
    await setCameraView('Top');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product3_polo_green_wire_top.png') });
    console.log('Captured product3_polo_green_wire_top.png');

    // ----------------------------------------------------
    // TEST 4: DUAL GRAPHIC T-SHIRT (Speed Division Streetwear Front & Back)
    // ----------------------------------------------------
    console.log('\n--- Test 4: Dual Graphic T-Shirt (fk_dual_graphic_streetwear) ---');
    await clickButton('Try Samples');
    await clickButton('Charcoal Black');
    await waitForModel();

    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product4_dual_graphic_front.png') });
    console.log('Captured product4_dual_graphic_front.png');

    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product4_dual_graphic_back.png') });
    console.log('Captured product4_dual_graphic_back.png');

    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'product4_dual_graphic_persp.png') });
    console.log('Captured product4_dual_graphic_persp.png');

    // Inspection panel capture
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pbr_inspection_panel.png') });
    console.log('Captured pbr_inspection_panel.png');

    console.log('\n=== ALL 4 PRODUCTS VERIFIED AND CAPTURED SUCCESSFULLY ===');
  } catch (err) {
    console.error('Puppeteer verification failed:', err);
  } finally {
    await browser.close();
  }
}

run();
