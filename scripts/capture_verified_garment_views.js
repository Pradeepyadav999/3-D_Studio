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
  console.log('Capturing verified garment views in live studio...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1600,1050',
      '--user-data-dir=/tmp/chrome-verified-studio',
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

    // Click "Try Samples" tab
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const sampleBtn = btns.find(b => b.innerText.includes('Try Samples'));
      if (sampleBtn) sampleBtn.click();
    });
    await sleep(1500);

    // Select the black graphic crew neck product (fk_graphic_crew_black)
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const blackProduct = buttons.find(b => b.innerText.includes('Onyx Black') || b.innerText.includes('Pacific Coastline'));
      if (blackProduct) blackProduct.click();
    });
    await sleep(1500);

    // Click "Generate 3D Garment" button
    console.log('Clicking Generate 3D Garment...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const genBtn = buttons.find(b => b.innerText.includes('Generate 3D Garment') || b.innerText.includes('Regenerate 3D Model'));
      if (genBtn) genBtn.click();
    });

    // Wait for generation
    console.log('Waiting for generation to finish...');
    for (let i = 0; i < 40; i++) {
      const isGen = await page.evaluate(() => 
        document.body.textContent.includes('Generating 3D Garment') || 
        document.body.textContent.includes('Generating Geometry...')
      );
      if (!isGen) {
        console.log(`Generation completed at loop ${i}!`);
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
      await sleep(1000);
      return clicked;
    };

    // 1. FRONT VIEW - TEXTURED
    console.log('Capturing Front Textured...');
    await clickButton('Front');
    await clickButton('Textured');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_front_textured.png') });

    // 2. BACK VIEW - TEXTURED
    console.log('Capturing Back Textured...');
    await clickButton('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_back_textured.png') });

    // 3. LEFT VIEW - TEXTURED
    console.log('Capturing Left Textured...');
    await clickButton('Left');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_left_textured.png') });

    // 4. RIGHT VIEW - TEXTURED
    console.log('Capturing Right Textured...');
    await clickButton('Right');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_right_textured.png') });

    // 5. TOP VIEW - TEXTURED
    console.log('Capturing Top Textured...');
    await clickButton('Top');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_top_textured.png') });

    // 6. PERSPECTIVE - TEXTURED
    console.log('Capturing Perspective Textured...');
    await clickButton('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_persp_textured.png') });

    // 7. FRONT VIEW - SOLID
    console.log('Capturing Front Solid...');
    await clickButton('Front');
    await clickButton('Solid');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_front_solid.png') });

    // 8. BACK VIEW - SOLID
    console.log('Capturing Back Solid...');
    await clickButton('Back');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_back_solid.png') });

    // 9. TOP VIEW - SOLID
    console.log('Capturing Top Solid...');
    await clickButton('Top');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_top_solid.png') });

    // 10. LEFT VIEW - SOLID
    console.log('Capturing Left Solid...');
    await clickButton('Left');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_left_solid.png') });

    // 11. FRONT VIEW - WIREFRAME
    console.log('Capturing Front Wireframe...');
    await clickButton('Front');
    await clickButton('Wireframe');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_front_wireframe.png') });

    // 12. PERSPECTIVE - WIREFRAME
    console.log('Capturing Perspective Wireframe...');
    await clickButton('Perspective');
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'verified_persp_wireframe.png') });

    console.log('All verified views successfully captured!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Puppeteer run error:', err);
  process.exit(1);
});
