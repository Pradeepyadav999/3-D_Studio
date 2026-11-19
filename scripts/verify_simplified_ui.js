import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900', '--user-data-dir=/tmp/chrome-ui-verify'],
    defaultViewport: { width: 1440, height: 900 }
  });

  try {
    const page = await browser.newPage();
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2500));

    // Verify initial layout with preloaded chart
    console.log('Verifying initial studio state...');
    await page.screenshot({ path: path.join(DOCS_DIR, 'simplified_ui_initial.png') });

    // Verify measurement table rows
    const tableInfo = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('table tbody tr')).map(tr => {
        const label = tr.querySelector('td:first-child')?.textContent?.trim();
        const inputs = Array.from(tr.querySelectorAll('input')).map(inp => inp.value);
        return { label, inputs };
      });
      return rows;
    });
    console.log('Table Rows:', JSON.stringify(tableInfo, null, 2));

    // Verify Fine-Tune Geometry is NOT present
    const hasFineTune = await page.evaluate(() => {
      return document.body.textContent.includes('Fine-Tune Geometry');
    });
    console.log('Contains Fine-Tune Geometry (should be false):', hasFineTune);

    // Click XXL in the dedicated size selector
    console.log('Selecting Size XXL...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const xxlBtn = buttons.find(b => b.textContent && b.textContent.trim().startsWith('XXL'));
      if (xxlBtn) xxlBtn.click();
    });
    await new Promise(r => setTimeout(r, 1000));

    // Check if generating or generated
    console.log('Waiting for XXL model generation / load...');
    await page.waitForFunction(() => {
      const exportBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Download GLB'));
      return exportBtn && !exportBtn.disabled;
    }, { timeout: 35000 });

    await new Promise(r => setTimeout(r, 2000));

    // Capture screenshot of Size XXL loaded in simplified UI
    console.log('Capturing Size XXL screenshot...');
    await page.screenshot({ path: path.join(DOCS_DIR, 'simplified_ui_xxl.png') });

    // Check Right Panel properties
    const rightPanelInfo = await page.evaluate(() => {
      const panel = document.querySelector('.w-72, .w-80');
      return panel ? panel.innerText : 'Not found';
    });
    console.log('Right Panel Content:\n', rightPanelInfo);

    console.log('Verification completed successfully!');
  } finally {
    await browser.close();
  }
}

run().catch(console.error);
