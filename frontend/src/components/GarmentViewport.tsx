import React, { useEffect, useRef, useState } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { ShadingMode, ViewPreset, ModelMetadata } from '../types/garment';
import { ViewportToolbar } from './ViewportToolbar';
import { MetricGrid } from './MetricGrid';
import { GarmentDimensionOverlays } from './GarmentDimensionOverlays';
import { MeasurementAccuracyModal } from './MeasurementAccuracyModal';
import { Shirt, Loader2, Compass, AlertCircle } from 'lucide-react';

interface GarmentViewportProps {
  modelUrl: string | null;
  textureUrl?: string | null;
  metadata: ModelMetadata | null;
  isGenerating: boolean;
  generationProgress: number;
  selectedSize: string;
  shadingMode?: ShadingMode;
  onShadingModeChange?: (mode: ShadingMode) => void;
}

// Subcomponent: Loads and manipulates the real GLB Mesh with 4 distinct view modes
const LoadedGarment: React.FC<{
  url: string;
  textureUrl?: string | null;
  shadingMode: ShadingMode;
  showBoundingBox: boolean;
  onLoaded: (box: THREE.Box3, yOffset: number) => void;
  onTextureStatus: (hasTexture: boolean) => void;
  yOffset: number;
}> = ({ url, textureUrl, shadingMode, showBoundingBox, onLoaded, onTextureStatus, yOffset }) => {
  const [gltfScene, setGltfScene] = useState<THREE.Group | null>(null);
  const [wireframeOverlay, setWireframeOverlay] = useState<THREE.Group | null>(null);

  useEffect(() => {
    let isCancelled = false;
    const loader = new GLTFLoader();

    loader.load(
      url,
      (gltf) => {
        if (isCancelled) return;
        const root = gltf.scene;
        const wireOverlayGroup = new THREE.Group();
        let foundEmbeddedTexture = false;

        root.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.castShadow = true;
            mesh.receiveShadow = true;

            // 1. PBR Textured Material from GLB
            const origMat = mesh.material;
            if (Array.isArray(origMat)) {
              origMat.forEach((m) => {
                m.side = THREE.DoubleSide;
                if ((m as any).map) {
                  (m as any).map.colorSpace = THREE.SRGBColorSpace;
                  (m as any).map.needsUpdate = true;
                  foundEmbeddedTexture = true;
                }
              });
              mesh.userData.origMaterial = origMat;
            } else if (origMat) {
              origMat.side = THREE.DoubleSide;
              if ((origMat as any).map) {
                (origMat as any).map.colorSpace = THREE.SRGBColorSpace;
                (origMat as any).map.needsUpdate = true;
                foundEmbeddedTexture = true;
              }
              mesh.userData.origMaterial = origMat;
            }

            // Fallback load from textureUrl if GLB embedded map was missing
            if (!foundEmbeddedTexture && textureUrl) {
              const texLoader = new THREE.TextureLoader();
              texLoader.load(
                textureUrl,
                (loadedTex) => {
                  loadedTex.colorSpace = THREE.SRGBColorSpace;
                  if (mesh.userData.origMaterial) {
                    if (Array.isArray(mesh.userData.origMaterial)) {
                      mesh.userData.origMaterial.forEach((m: any) => {
                        m.map = loadedTex;
                        m.needsUpdate = true;
                      });
                    } else {
                      (mesh.userData.origMaterial as any).map = loadedTex;
                      mesh.userData.origMaterial.needsUpdate = true;
                    }
                    onTextureStatus(true);
                  }
                },
                undefined,
                (err) => console.warn('TextureLoader fallback error:', err)
              );
            }

            // 2. Neutral Solid Material (Clean Studio Clay for proportions & silhouette inspection)
            const solidMat = new THREE.MeshStandardMaterial({
              color: new THREE.Color(0xd6dade),
              roughness: 0.78,
              metalness: 0.04,
              side: THREE.DoubleSide,
            });
            mesh.userData.solidMaterial = solidMat;

            // 3. Pure Wireframe Material (Vibrant sky-blue for mesh density & topology inspection)
            const wireOnlyMat = new THREE.MeshBasicMaterial({
              color: 0x38bdf8,
              wireframe: true,
              side: THREE.DoubleSide,
            });
            mesh.userData.wireOnlyMaterial = wireOnlyMat;

            // 4. Wireframe Overlay Clone (Darker royal blue overlay for SOLID + WIRE mode)
            const wireOverlayMat = new THREE.MeshBasicMaterial({
              color: 0x1d4ed8,
              wireframe: true,
              transparent: true,
              opacity: 0.65,
              depthTest: true,
            });
            const wireMesh = new THREE.Mesh(mesh.geometry, wireOverlayMat);
            wireMesh.position.copy(mesh.position);
            wireMesh.rotation.copy(mesh.rotation);
            wireMesh.scale.copy(mesh.scale);
            wireOverlayGroup.add(wireMesh);
          }
        });

        onTextureStatus(foundEmbeddedTexture || !!textureUrl);

        // Compute Bounding Box STRICTLY from the garment meshes (ignoring any helpers)
        const meshBbox = new THREE.Box3();
        root.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            meshBbox.expandByObject(child);
          }
        });

        // Calculate offset so garment hem rests on Y = 0.0
        const calculatedYOffset = -meshBbox.min.y;
        const worldBbox = meshBbox.clone().applyMatrix4(
          new THREE.Matrix4().makeTranslation(0, calculatedYOffset, 0)
        );

        onLoaded(worldBbox, calculatedYOffset);

        setGltfScene(root);
        setWireframeOverlay(wireOverlayGroup);
      },
      undefined,
      (err) => {
        console.error('Error loading GLB:', err);
      }
    );

    return () => {
      isCancelled = true;
    };
  }, [url, textureUrl]);

  // Update material on shading mode change (Zero reload, zero regeneration!)
  useEffect(() => {
    if (!gltfScene) return;
    gltfScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const origMat = mesh.userData.origMaterial;
        const solidMat = mesh.userData.solidMaterial;
        const wireOnlyMat = mesh.userData.wireOnlyMaterial;

        if (shadingMode === 'textured') {
          if (origMat) {
            mesh.material = origMat;
            if (Array.isArray(origMat)) {
              origMat.forEach((m) => {
                m.wireframe = false;
                m.needsUpdate = true;
              });
            } else {
              origMat.wireframe = false;
              origMat.needsUpdate = true;
            }
          }
        } else if (shadingMode === 'solid') {
          if (solidMat) {
            solidMat.wireframe = false;
            solidMat.needsUpdate = true;
            mesh.material = solidMat;
          }
        } else if (shadingMode === 'wireframe') {
          if (wireOnlyMat) {
            mesh.material = wireOnlyMat;
          }
        } else if (shadingMode === 'solid_wireframe') {
          if (solidMat) {
            solidMat.wireframe = false;
            solidMat.needsUpdate = true;
            mesh.material = solidMat;
          }
        }
      }
    });
  }, [shadingMode, gltfScene]);

  if (!gltfScene) return null;

  return (
    <group position={[0, yOffset, 0]}>
      <primitive object={gltfScene} />
      {shadingMode === 'solid_wireframe' && wireframeOverlay && (
        <primitive object={wireframeOverlay} />
      )}
      {showBoundingBox && <primitive object={new THREE.BoxHelper(gltfScene, 0x00f0ff)} />}
    </group>
  );
};

// Subcomponent: Precision Camera Framing Controller
// Uses actual garment mesh bounds only — independent of helpers or grid!
const CameraController: React.FC<{
  viewPreset: ViewPreset;
  controlsRef: React.RefObject<any>;
  triggerReset: number;
  triggerFit: number;
  boundingBox: THREE.Box3 | null;
}> = ({ viewPreset, controlsRef, triggerReset, triggerFit, boundingBox }) => {
  const { camera, size: viewportSize } = useThree();

  const applyViewPreset = (view: ViewPreset) => {
    const controls = controlsRef.current;
    if (!controls) return;

    // Use actual garment mesh bounding box to find center and dimensions
    const center = boundingBox
      ? boundingBox.getCenter(new THREE.Vector3())
      : new THREE.Vector3(0, 0.37, 0);

    const size = boundingBox
      ? boundingBox.getSize(new THREE.Vector3())
      : new THREE.Vector3(0.80, 0.74, 0.20);

    // Camera field of view calculations
    const fov = (camera as THREE.PerspectiveCamera).fov || 40;
    const halfFovRad = (fov / 2) * (Math.PI / 180);
    const aspect = Math.max(0.5, viewportSize.width / Math.max(1, viewportSize.height));

    // Padding factor so the T-shirt occupies 78-82% of the viewport (crisp & hero-sized)
    const padding = 1.22;

    // Set camera target to the exact 3D center of the garment
    controls.target.copy(center);

    switch (view) {
      case 'front': {
        const distY = (size.y / 2) / Math.tan(halfFovRad);
        const distX = (size.x / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distY, distX) * padding;
        camera.position.set(center.x, center.y, center.z - dist);
        break;
      }
      case 'back': {
        const distY = (size.y / 2) / Math.tan(halfFovRad);
        const distX = (size.x / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distY, distX) * padding;
        camera.position.set(center.x, center.y, center.z + dist);
        break;
      }
      case 'left': {
        const distY = (size.y / 2) / Math.tan(halfFovRad);
        const distZ = (size.z / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distY, distZ) * padding;
        camera.position.set(center.x - dist, center.y, center.z);
        break;
      }
      case 'right': {
        const distY = (size.y / 2) / Math.tan(halfFovRad);
        const distZ = (size.z / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distY, distZ) * padding;
        camera.position.set(center.x + dist, center.y, center.z);
        break;
      }
      case 'top': {
        const distZ = (size.z / 2) / Math.tan(halfFovRad);
        const distX = (size.x / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distZ, distX) * padding;
        camera.position.set(center.x, center.y + dist, center.z - 0.0001);
        break;
      }
      case 'perspective':
      default: {
        const distY = (size.y / 2) / Math.tan(halfFovRad);
        const distX = (size.x / 2) / (Math.tan(halfFovRad) * aspect);
        const dist = Math.max(distY, distX) * padding;
        camera.position.set(
          center.x - dist * 0.65,
          center.y + dist * 0.22,
          center.z - dist * 0.85
        );
        break;
      }
    }
    controls.update();
  };

  useEffect(() => {
    applyViewPreset(viewPreset);
  }, [viewPreset, boundingBox]);

  useEffect(() => {
    (window as any).__setViewportCamera = (camX: number, camY: number, camZ: number, targetX: number, targetY: number, targetZ: number) => {
      const controls = controlsRef.current;
      if (!controls) return;
      controls.target.set(targetX, targetY, targetZ);
      camera.position.set(camX, camY, camZ);
      controls.update();
    };
  }, [camera, controlsRef]);

  useEffect(() => {
    if (triggerReset > 0) {
      applyViewPreset('perspective');
    }
  }, [triggerReset]);

  useEffect(() => {
    if (triggerFit > 0) {
      applyViewPreset(viewPreset);
    }
  }, [triggerFit]);

  return null;
};

export const GarmentViewport: React.FC<GarmentViewportProps> = ({
  modelUrl,
  textureUrl,
  metadata,
  isGenerating,
  generationProgress,
  selectedSize,
  shadingMode: propShadingMode,
  onShadingModeChange: propOnShadingModeChange,
}) => {
  const controlsRef = useRef<any>(null);
  const [localShadingMode, setLocalShadingMode] = useState<ShadingMode>('textured');
  const [viewPreset, setViewPreset] = useState<ViewPreset>('perspective');
  const [showGrid, setShowGrid] = useState(true);
  const [showBoundingBox, setShowBoundingBox] = useState(false);
  // Default: Normal View Mode (false) - Hero T-shirt, no measurement clutter!
  const [isValidationMode, setIsValidationMode] = useState<boolean>(false);
  const [showAccuracyModal, setShowAccuracyModal] = useState<boolean>(false);
  const [resetTrigger, setResetTrigger] = useState(0);
  const [fitTrigger, setFitTrigger] = useState(0);
  const [currentBox, setCurrentBox] = useState<THREE.Box3 | null>(null);
  const [garmentYOffset, setGarmentYOffset] = useState<number>(0);
  const [hasTexture, setHasTexture] = useState<boolean>(true);

  const activeShadingMode = propShadingMode || localShadingMode;
  const handleShadingChange = (mode: ShadingMode) => {
    if (propOnShadingModeChange) {
      propOnShadingModeChange(mode);
    } else {
      setLocalShadingMode(mode);
    }
  };

  const handleGarmentLoaded = (box: THREE.Box3, yOffset: number) => {
    setCurrentBox(box);
    setGarmentYOffset(yOffset);
  };

  return (
    <div className="relative w-full h-full bg-studio-950 overflow-hidden select-none flex flex-col">
      {/* 1. VIEWPORT TOOLBAR (Positioned directly above 3D viewport canvas) */}
      <ViewportToolbar
        shadingMode={activeShadingMode}
        onShadingModeChange={handleShadingChange}
        viewPreset={viewPreset}
        onViewPresetChange={setViewPreset}
        onResetCamera={() => setResetTrigger((n) => n + 1)}
        onFitModel={() => setFitTrigger((n) => n + 1)}
        showGrid={showGrid}
        onToggleGrid={() => setShowGrid(!showGrid)}
        showBoundingBox={showBoundingBox}
        onToggleBoundingBox={() => setShowBoundingBox(!showBoundingBox)}
        showDimensions={isValidationMode}
        onToggleDimensions={() => setIsValidationMode(!isValidationMode)}
        onOpenAccuracyReport={() => setShowAccuracyModal(true)}
        hasModel={!!modelUrl}
        hasTexture={hasTexture}
      />

      {/* 2. TEXTURE WARNING / SUCCESS BADGE */}
      {modelUrl && activeShadingMode === 'textured' && !hasTexture && (
        <div className="absolute top-14 left-4 z-20 bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs px-3 py-1.5 rounded-lg flex items-center space-x-2 backdrop-blur-md shadow-lg">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>Texture artwork not found in GLB. Falling back to neutral solid.</span>
        </div>
      )}

      {/* Mode Indicator Pill in top right */}
      {modelUrl && (
        <div className="absolute top-14 right-4 z-20 pointer-events-none">
          <div className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-bold tracking-wider uppercase border backdrop-blur-md transition-all ${
            isValidationMode
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-lg ring-1 ring-amber-400/30'
              : 'bg-studio-900/60 text-studio-400 border-studio-800'
          }`}>
            {isValidationMode ? 'Validation Mode: Calibrated 3D Measurements Active' : 'Normal Studio Mode: Clean Product Preview'}
          </div>
        </div>
      )}

      {/* 3. MAIN 3D THREE.JS CANVAS */}
      <div className="flex-1 relative w-full h-full overflow-hidden">
        <Canvas
          shadows
          camera={{ position: [0, 0.37, -1.25], fov: 40 }}
          gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
          className="w-full h-full"
        >
          <color attach="background" args={['#0e1013']} />

          {/* Ambient & Studio Lights */}
          <ambientLight intensity={0.7} />
          <directionalLight
            position={[5, 8, 5]}
            intensity={1.2}
            castShadow
            shadow-mapSize-width={2048}
            shadow-mapSize-height={2048}
            shadow-camera-near={0.5}
            shadow-camera-far={20}
            shadow-bias={-0.0001}
          />
          <directionalLight position={[-5, 4, -4]} intensity={0.6} color="#94a3b8" />
          <directionalLight position={[0, -4, 4]} intensity={0.3} color="#64748b" />

          {/* Calibrated Metric Floor Grid (Subtle in normal mode; full 1cm/10cm & ruler in validation mode) */}
          <MetricGrid visible={showGrid} isValidationMode={isValidationMode} />

          {/* Contact Shadow under model */}
          {modelUrl && (
            <ContactShadows
              position={[0, -0.001, 0]}
              opacity={0.6}
              scale={2.2}
              blur={2}
              far={1.5}
              color="#000000"
            />
          )}

          {/* The Real Generated 3D GLB Garment - NEVER affected by helpers */}
          {modelUrl ? (
            <LoadedGarment
              url={modelUrl}
              textureUrl={textureUrl}
              shadingMode={activeShadingMode}
              showBoundingBox={showBoundingBox}
              yOffset={garmentYOffset}
              onLoaded={handleGarmentLoaded}
              onTextureStatus={setHasTexture}
            />
          ) : null}

          {/* Independent 3D Dimension Overlays Group - Rendered only in validation mode */}
          {modelUrl && (
            <group position={[0, garmentYOffset, 0]}>
              <GarmentDimensionOverlays
                metadata={metadata || null}
                boundingBox={currentBox}
                visible={isValidationMode}
              />
            </group>
          )}

          {/* Camera Orbit Controls */}
          <OrbitControls
            ref={controlsRef}
            makeDefault
            enableDamping
            dampingFactor={0.06}
            minDistance={0.3}
            maxDistance={4.5}
            maxPolarAngle={Math.PI / 2 + 0.1}
          />

          {/* Camera Preset & Framing Controller */}
          <CameraController
            viewPreset={viewPreset}
            controlsRef={controlsRef}
            triggerReset={resetTrigger}
            triggerFit={fitTrigger}
            boundingBox={currentBox}
          />
        </Canvas>
      </div>

      {/* Generation Progress Overlay */}
      {isGenerating && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center z-30 select-none">
          <div className="bg-studio-900 border border-studio-700 p-6 rounded-xl shadow-2xl max-w-sm w-full mx-4 space-y-4 text-center">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mx-auto text-blue-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">Generating Parametric 3D Model</h4>
              <p className="text-xs text-studio-400 mt-1">Blender Python BMesh Engine running...</p>
            </div>
            <div className="space-y-1">
              <div className="w-full bg-studio-800 rounded-full h-2 overflow-hidden border border-studio-700">
                <div
                  className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${generationProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-studio-400">
                <span>Lofting Torso & Sleeves</span>
                <span>{generationProgress}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State Overlay before model generation */}
      {!modelUrl && !isGenerating && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10 p-6 text-center">
          <div className="max-w-md bg-studio-900/80 backdrop-blur-md border border-studio-800 p-6 rounded-2xl shadow-2xl space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mx-auto text-blue-400 shadow-inner">
              <Shirt className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-white">Interactive 3D Garment Viewport</h3>
            <p className="text-xs text-studio-300 leading-relaxed">
              Select an apparel product on the left or upload custom photos, and click{' '}
              <span className="text-blue-400 font-semibold">Generate 3D Garment</span> to construct the standalone 3D T-shirt in Blender.
            </p>
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-studio-800 text-[11px] font-mono text-studio-400 border border-studio-700">
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
              <span>Full orbit, zoom, pan, and 4 inspection view modes</span>
            </div>
          </div>
        </div>
      )}

      {/* Measurement Accuracy Audit Modal */}
      <MeasurementAccuracyModal
        isOpen={showAccuracyModal}
        onClose={() => setShowAccuracyModal(false)}
        metadata={metadata}
      />
    </div>
  );
};
