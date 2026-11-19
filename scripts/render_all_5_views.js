import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DOCS_DIR = path.resolve('docs');
const ARTIFACTS_DIR = '/Users/pradeepyadav/.gemini/antigravity/brain/92cf68fb-6924-4547-a74f-c85242906261/images';

try { fs.mkdirSync(DOCS_DIR, { recursive: true }); } catch (e) {}
try { fs.mkdirSync(ARTIFACTS_DIR, { recursive: true }); } catch (e) {}

const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { margin: 0; background: #0c0d12; overflow: hidden; }
    canvas { width: 100vw; height: 100vh; display: block; }
  </style>
  <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
  <script src="https://unpkg.com/three@0.160.0/examples/js/loaders/GLTFLoader.js"></script>
</head>
<body>
<script>
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0c0d12);

  const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0.38, 2.3);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(2);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  document.body.appendChild(renderer.domElement);

  // Soft studio lighting
  const hemi = new THREE.HemisphereLight(0xffffff, 0x222233, 1.2);
  scene.add(hemi);

  const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
  keyLight.position.set(1.5, 2.5, 3);
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight(0xaaccff, 0.9);
  fillLight.position.set(-2, 1.5, 2);
  scene.add(fillLight);

  const backLight = new THREE.DirectionalLight(0xffeedd, 1.4);
  backLight.position.set(0, 2, -3);
  scene.add(backLight);

  // Subtle floor grid
  const grid = new THREE.GridHelper(4, 20, 0x334466, 0x182030);
  grid.position.y = -0.38;
  scene.add(grid);

  let currentModel = null;
  const loader = new THREE.GLTFLoader();

  window.loadGLB = function(url, callback) {
    loader.load(url, function(gltf) {
      if (currentModel) scene.remove(currentModel);
      currentModel = gltf.scene;

      // Center model
      const box = new THREE.Box3().setFromObject(currentModel);
      const center = box.getCenter(new THREE.Vector3());
      currentModel.position.x -= center.x;
      currentModel.position.y -= center.y;
      currentModel.position.z -= center.z;

      currentModel.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          if (child.material) {
            child.material.roughness = 0.72;
            child.material.metalness = 0.05;
          }
        }
      });

      scene.add(currentModel);
      renderer.render(scene, camera);
      if (callback) callback();
    });
  };

  window.setView = function(viewName, isWireframe) {
    if (!currentModel) return;

    currentModel.traverse((child) => {
      if (child.isMesh && child.material) {
        child.material.wireframe = !!isWireframe;
      }
    });

    const dist = 2.15;
    if (viewName === 'front') {
      camera.position.set(0, 0, dist);
      camera.lookAt(0, 0, 0);
    } else if (viewName === 'back') {
      camera.position.set(0, 0, -dist);
      camera.lookAt(0, 0, 0);
    } else if (viewName === 'left') {
      camera.position.set(-dist, 0, 0);
      camera.lookAt(0, 0, 0);
    } else if (viewName === 'right') {
      camera.position.set(dist, 0, 0);
      camera.lookAt(0, 0, 0);
    } else if (viewName === 'top') {
      camera.position.set(0, dist * 1.05, 0.01);
      camera.lookAt(0, 0, 0);
    } else if (viewName === 'perspective') {
      camera.position.set(0.9, 0.6, 1.8);
      camera.lookAt(0, -0.05, 0);
    }
    renderer.render(scene, camera);
  };
</script>
</body>
</html>
`;

fs.writeFileSync('/tmp/three_5views_viewer.html', htmlContent);

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('Launching Chrome to render authentic 5 views...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1200,1000',
      '--user-data-dir=/tmp/chrome-5views',
      '--enable-webgl',
      '--use-gl=angle',
      '--use-angle=metal'
    ],
    defaultViewport: { width: 1200, height: 1000 }
  });

  try {
    const page = await browser.newPage();
    await page.goto('file:///tmp/three_5views_viewer.html', { waitUntil: 'load' });
    await sleep(1500);

    // Copy model to a web-accessible / tmp directory
    fs.copyFileSync('storage/test_authentic_tshirt.glb', '/tmp/model.glb');

    // Load model via data URI
    const glbBuffer = fs.readFileSync('storage/test_authentic_tshirt.glb');
    const dataUri = `data:model/gltf-binary;base64,${glbBuffer.toString('base64')}`;

    console.log('Loading 3D model into Three.js...');
    await page.evaluate((uri) => {
      return new Promise((resolve) => {
        window.loadGLB(uri, () => resolve());
      });
    }, dataUri);

    await sleep(1000);

    const views = [
      { name: 'front', wire: false, file: 'view_1_front.png' },
      { name: 'back', wire: false, file: 'view_2_back.png' },
      { name: 'left', wire: false, file: 'view_3_left.png' },
      { name: 'right', wire: false, file: 'view_4_right.png' },
      { name: 'top', wire: false, file: 'view_5_top.png' },
      { name: 'front', wire: true, file: 'view_6_front_wireframe.png' },
      { name: 'perspective', wire: false, file: 'view_7_perspective.png' },
    ];

    for (const v of views) {
      await page.evaluate((viewName, isWire) => {
        window.setView(viewName, isWire);
      }, v.name, v.wire);
      await sleep(400);

      const filePath = path.join(DOCS_DIR, v.file);
      await page.screenshot({ path: filePath });
      console.log(`Rendered: ${v.file}`);
      fs.copyFileSync(filePath, path.join(ARTIFACTS_DIR, v.file));
    }

    console.log('All 5 views rendered successfully!');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error('Render error:', err);
  process.exit(1);
});
