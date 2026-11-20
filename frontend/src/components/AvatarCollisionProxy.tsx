import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { AvatarStyle } from '../types/garment';

interface AvatarCollisionProxyProps {
  visible: boolean;
  avatarStyle: AvatarStyle;
  avatarOpacity?: number;
  garmentDimensions?: {
    chest_cm: number;
    shoulder_cm: number;
    length_cm: number;
  } | null;
  garmentYOffset: number;
  onClearanceUpdate?: (clearance: { radial_ease_cm: number; shoulder_ease_cm: number; noPenetration: boolean }) => void;
}

export const AvatarCollisionProxy: React.FC<AvatarCollisionProxyProps> = ({
  visible,
  avatarStyle,
  avatarOpacity = 0.55,
  garmentDimensions,
  garmentYOffset,
  onClearanceUpdate,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const [avatarScene, setAvatarScene] = useState<THREE.Group | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  // Default target dimensions from garment (or standard M)
  const gChest = garmentDimensions?.chest_cm || 106.0;
  const gShoulder = garmentDimensions?.shoulder_cm || 49.0;
  const gLength = garmentDimensions?.length_cm || 71.0;

  // Calibrated Avatar Collision Proxy Dimensions (Strict 1.0 - 2.0 cm clearance)
  // Ensures avatar body sits strictly INSIDE the garment mesh without penetration
  const avatarChest = Math.max(82.0, gChest - 4.5); // 4.5 cm circumference ease (~7.2 mm radial gap)
  const avatarShoulder = Math.max(38.0, gShoulder - 2.2); // 2.2 cm span ease (1.1 cm per shoulder tip)
  const avatarLength = gLength;

  const radialEase = (gChest - avatarChest) / (2 * Math.PI);
  const shoulderEase = (gShoulder - avatarShoulder) / 2.0;

  useEffect(() => {
    if (onClearanceUpdate) {
      onClearanceUpdate({
        radial_ease_cm: Number(radialEase.toFixed(2)),
        shoulder_ease_cm: Number(shoulderEase.toFixed(2)),
        noPenetration: radialEase > 0.4 && shoulderEase > 0.4,
      });
    }
  }, [radialEase, shoulderEase, onClearanceUpdate]);

  // Load Avatar GLB Model
  useEffect(() => {
    let isCancelled = false;
    const loader = new GLTFLoader();
    const modelUrl = '/avatar_mannequin_proxy.glb';

    loader.load(
      modelUrl,
      (gltf) => {
        if (isCancelled) return;
        const root = gltf.scene;

        root.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.castShadow = true;
            mesh.receiveShadow = true;
          }
        });

        setAvatarScene(root);
        setLoadFailed(false);
      },
      undefined,
      (err) => {
        console.warn('Avatar GLB load fallback to procedural avatar:', err);
        setLoadFailed(true);
      }
    );

    return () => {
      isCancelled = true;
    };
  }, []);

  // Update Materials based on avatarStyle & avatarOpacity
  useEffect(() => {
    if (!avatarScene) return;

    avatarScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;

        if (avatarStyle === 'solid') {
          // Charcoal Slate Studio Mannequin Clay
          mesh.material = new THREE.MeshStandardMaterial({
            color: new THREE.Color(0x28303d),
            roughness: 0.65,
            metalness: 0.12,
            side: THREE.DoubleSide,
            transparent: false,
            opacity: 1.0,
          });
        } else if (avatarStyle === 'translucent') {
          // Vibrant Cyan Ghost Collision Proxy for checking clearance inside fabric
          mesh.material = new THREE.MeshStandardMaterial({
            color: new THREE.Color(0x38bdf8),
            roughness: 0.4,
            metalness: 0.05,
            transparent: true,
            opacity: avatarOpacity,
            depthWrite: false,
            side: THREE.DoubleSide,
          });
        } else if (avatarStyle === 'wireframe') {
          // Pure Cyan Geometric Collision Wireframe
          mesh.material = new THREE.MeshBasicMaterial({
            color: new THREE.Color(0x06b6d4),
            wireframe: true,
            side: THREE.DoubleSide,
          });
        }
      }
    });
  }, [avatarScene, avatarStyle, avatarOpacity]);

  // Compute scale factors relative to master avatar reference
  // Master avatar was generated with: chest 101.5 cm, shoulder 46.8 cm, height 100.6 cm
  const scaleX = avatarShoulder / 46.8;
  const scaleY = avatarLength / 71.0;
  const scaleZ = avatarChest / 101.5;

  if (!visible) return null;

  return (
    <group ref={groupRef} position={[0, garmentYOffset, 0]}>
      {avatarScene && !loadFailed ? (
        <group scale={[scaleX, scaleY, scaleZ]}>
          <primitive object={avatarScene} />
        </group>
      ) : (
        /* Procedural Mannequin Fallback (Always guaranteed to render) */
        <ProceduralMannequin
          avatarStyle={avatarStyle}
          avatarOpacity={avatarOpacity}
          chestRadius={(avatarChest / (2 * Math.PI)) * 0.01}
          shoulderHalfWidth={(avatarShoulder / 200.0)}
          torsoHeight={avatarLength * 0.01}
        />
      )}
    </group>
  );
};

// Procedural 3D Athletic Mannequin Component (Anatomical fallback)
const ProceduralMannequin: React.FC<{
  avatarStyle: AvatarStyle;
  avatarOpacity: number;
  chestRadius: number;
  shoulderHalfWidth: number;
  torsoHeight: number;
}> = ({ avatarStyle, avatarOpacity, chestRadius, shoulderHalfWidth, torsoHeight }) => {
  const material = useMemo(() => {
    if (avatarStyle === 'solid') {
      return new THREE.MeshStandardMaterial({
        color: new THREE.Color(0x28303d),
        roughness: 0.65,
        metalness: 0.12,
      });
    } else if (avatarStyle === 'translucent') {
      return new THREE.MeshStandardMaterial({
        color: new THREE.Color(0x38bdf8),
        roughness: 0.4,
        transparent: true,
        opacity: avatarOpacity,
        depthWrite: false,
      });
    } else {
      return new THREE.MeshBasicMaterial({
        color: new THREE.Color(0x06b6d4),
        wireframe: true,
      });
    }
  }, [avatarStyle, avatarOpacity]);

  const underarmZ = torsoHeight * 0.70;
  const neckZ = torsoHeight;

  return (
    <group>
      {/* 1. Torso Body */}
      <mesh position={[0, torsoHeight * 0.48, 0]} material={material}>
        <cylinderGeometry
          args={[chestRadius * 0.98, chestRadius * 0.92, torsoHeight * 0.96, 32]}
        />
      </mesh>

      {/* 2. Upper Chest & Clavicle */}
      <mesh position={[0, torsoHeight * 0.88, 0]} material={material}>
        <cylinderGeometry
          args={[chestRadius * 0.75, chestRadius * 0.98, torsoHeight * 0.22, 32]}
        />
      </mesh>

      {/* 3. Neck & Head */}
      <mesh position={[0, neckZ + 0.045, 0]} material={material}>
        <cylinderGeometry args={[0.055, 0.060, 0.09, 24]} />
      </mesh>
      <mesh position={[0, neckZ + 0.165, 0.01]} material={material}>
        <sphereGeometry args={[0.092, 32, 24]} />
      </mesh>

      {/* 4. Left Arm (A-Pose 65° drape down, 9° pitch forward) */}
      <group
        position={[-shoulderHalfWidth, underarmZ + 0.08, 0]}
        rotation={[THREE.MathUtils.degToRad(9), 0, THREE.MathUtils.degToRad(25)]}
      >
        <mesh position={[0, -0.14, 0]} material={material}>
          <cylinderGeometry args={[0.048, 0.040, 0.28, 16]} />
        </mesh>
      </group>

      {/* 5. Right Arm (A-Pose 65° drape down, 9° pitch forward) */}
      <group
        position={[shoulderHalfWidth, underarmZ + 0.08, 0]}
        rotation={[THREE.MathUtils.degToRad(9), 0, THREE.MathUtils.degToRad(-25)]}
      >
        <mesh position={[0, -0.14, 0]} material={material}>
          <cylinderGeometry args={[0.048, 0.040, 0.28, 16]} />
        </mesh>
      </group>

      {/* 6. Tailor's Studio Pedestal Hem Base */}
      <mesh position={[0, 0.015, 0]} material={material}>
        <cylinderGeometry args={[chestRadius * 0.92, chestRadius * 0.96, 0.03, 32]} />
      </mesh>
    </group>
  );
};
