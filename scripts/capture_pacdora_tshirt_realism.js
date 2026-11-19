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
  console.log('=== STARTING PACDORA-STYLE 3D T-SHIRT REALISM CAPTURE ===');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1100',
      '--user-data-dir=/tmp/chrome-pacdora-studio',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1600, height: 1100 }
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
      await sleep(1000);
    };

    const setShadingMode = async (modeName) => {
      await page.evaluate((mode) => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.innerText.toLowerCase().includes(mode.toLowerCase()));
        if (btn) btn.click();
      }, modeName);
      await sleep(1000);
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
      await sleep(2500);
    };

    // ----------------------------------------------------
    // PACDORA REALISM TEST 1: Plain Regular Crew T-Shirt (Lavender)
    // Demonstrates clean organic torso shape, collar thickness, hem curves, and cloth drape
    // ----------------------------------------------------
    console.log('\n--- Capturing Plain Regular Crew T-Shirt (Lavender) ---');
    await clickButton('Try Samples');
    await clickButton('Lavender');
    await waitForModel();

    // 1. Textured Front View
    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_front_textured.png') });
    console.log('Saved pacdora_crew_front_textured.png');

    // 2. Textured Back View
    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_back_textured.png') });
    console.log('Saved pacdora_crew_back_textured.png');

    // 3. Side View (profile silhouette, chest fullness, shoulder slope)
    await setCameraView('Left');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_side_left.png') });
    console.log('Saved pacdora_crew_side_left.png');

    // 4. Perspective Dynamic Studio View (Textured)
    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_persp_textured.png') });
    console.log('Saved pacdora_crew_persp_textured.png');

    // 5. Solid Clay Shading (Perspective - highlighting surface geometry and fabric curvature)
    await setShadingMode('Solid');
    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_solid_persp.png') });
    console.log('Saved pacdora_crew_solid_persp.png');

    // 6. Solid Clay Front View
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_solid_front.png') });
    console.log('Saved pacdora_crew_solid_front.png');

    // 7. Wireframe View (Clean 2-manifold grid topology)
    await setShadingMode('Wire');
    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_wire_persp.png') });
    console.log('Saved pacdora_crew_wire_persp.png');

    // 8. Solid + Wire View
    await setShadingMode('Solid + Wire');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_crew_solid_wire_front.png') });
    console.log('Saved pacdora_crew_solid_wire_front.png');

    // ----------------------------------------------------
    // PACDORA REALISM TEST 2: Graphic Crew T-Shirt (Onyx Black with chest graphic)
    // Verifies 0% graphic distortion, ink tactile relief, and collar ribbing
    // ----------------------------------------------------
    console.log('\n--- Capturing Graphic Crew T-Shirt (Onyx Black) ---');
    await clickButton('Try Samples');
    await clickButton('Onyx Black');
    await waitForModel();

    await setShadingMode('Textured');
    await setCameraView('Front');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_graphic_front_textured.png') });
    console.log('Saved pacdora_graphic_front_textured.png');

    await setCameraView('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_graphic_back_textured.png') });
    console.log('Saved pacdora_graphic_back_textured.png');

    await setCameraView('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'pacdora_graphic_persp_textured.png') });
    console.log('Saved pacdora_graphic_persp_textured.png');

    console.log('\n=== PACDORA 3D T-SHIRT REALISM CAPTURE COMPLETE ===');
  } catch (err) {
    console.error('Capture failed with error:', err);
  } finally {
    await browser.close();
  }
}

run();
