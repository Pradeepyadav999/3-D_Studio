import React, { useMemo } from 'react';
import * as THREE from 'three';
import { Text, Billboard } from '@react-three/drei';
import { ModelMetadata } from '../types/garment';

interface DimensionOverlaysProps {
  metadata: ModelMetadata | null;
  boundingBox?: THREE.Box3 | null;
  visible?: boolean;
}

export const GarmentDimensionOverlays: React.FC<DimensionOverlaysProps> = ({
  metadata,
  boundingBox = null,
  visible = false,
}) => {
  if (!visible || !metadata) return null;

  const measM = metadata.measurements_in_meters || {};
  const chestM = measM.chest || (metadata.input_measurements?.chest ? metadata.input_measurements.chest * 0.01 : 1.0668);
  const shoulderM = measM.shoulder || (metadata.input_measurements?.shoulder ? metadata.input_measurements.shoulder * 0.01 : 0.4572);
  const lengthM = measM.length || (metadata.input_measurements?.length ? metadata.input_measurements.length * 0.01 : 0.7366);
  const sleeveM = measM.sleeve || (metadata.input_measurements?.sleeve ? metadata.input_measurements.sleeve * 0.01 : 0.20955);

  const chestCm = (chestM * 100).toFixed(1);
  const chestIn = (chestM * 39.3701).toFixed(1);

  const shoulderCm = (shoulderM * 100).toFixed(1);
  const shoulderIn = (shoulderM * 39.3701).toFixed(1);

  const lengthCm = (lengthM * 100).toFixed(1);
  const lengthIn = (lengthM * 39.3701).toFixed(1);

  const sleeveCm = (sleeveM * 100).toFixed(1);
  const sleeveIn = (sleeveM * 39.3701).toFixed(1);

  // Landmarks
  const armholeDepth = Math.max(0.18, shoulderM * 0.43);
  const zUnderarm = lengthM - armholeDepth;
  const slopeDrop = (shoulderM / 2.0 - (shoulderM / 2.0) * 0.40) * Math.tan((14.5 * Math.PI) / 180);
  const zShoulderTip = lengthM - slopeDrop;

  // Chest ring ellipse points
  const chestRingGeo = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    const N = 64;
    const a = (chestM / (2 * Math.PI)) * 1.55;
    const b = a / 2.45;
    for (let i = 0; i <= N; i++) {
      const th = (2 * Math.PI * i) / N;
      pts.push(new THREE.Vector3(a * Math.cos(th), zUnderarm, b * Math.sin(th)));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [chestM, zUnderarm]);

  return (
    <group position={[0, 0, 0]}>
      {/* 1. CHEST CIRCUMFERENCE OVERLAY */}
      <group>
        <lineLoop geometry={chestRingGeo}>
          <lineBasicMaterial color="#00f0ff" linewidth={2} />
        </lineLoop>
        {/* Dynamic camera-facing Billboard badge */}
        <Billboard position={[0, zUnderarm, 0.12]}>
          <mesh>
            <planeGeometry args={[0.26, 0.045]} />
            <meshBasicMaterial color="#030712" transparent opacity={0.88} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.PlaneGeometry(0.26, 0.045)]} />
            <lineBasicMaterial color="#00f0ff" />
          </lineSegments>
          <Text
            position={[0, 0, 0.002]}
            fontSize={0.016}
            color="#00f0ff"
            anchorX="center"
            anchorY="middle"
          >
            {`Chest: ${chestCm} cm (${chestIn}")`}
          </Text>
        </Billboard>
      </group>

      {/* 2. SHOULDER SEAM-TO-SEAM WIDTH OVERLAY */}
      <group position={[0, zShoulderTip + 0.02, 0.02]}>
        <line>
          <bufferGeometry
            attach="geometry"
            {...new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(-shoulderM / 2, 0, 0),
              new THREE.Vector3(shoulderM / 2, 0, 0),
            ])}
          />
          <lineBasicMaterial color="#f59e0b" linewidth={2} />
        </line>
        {/* End caps */}
        <mesh position={[-shoulderM / 2, 0, 0]}>
          <boxGeometry args={[0.002, 0.025, 0.002]} />
          <meshBasicMaterial color="#f59e0b" />
        </mesh>
        <mesh position={[shoulderM / 2, 0, 0]}>
          <boxGeometry args={[0.002, 0.025, 0.002]} />
          <meshBasicMaterial color="#f59e0b" />
        </mesh>
        {/* Dynamic camera-facing Billboard badge */}
        <Billboard position={[0, 0.035, 0]}>
          <mesh>
            <planeGeometry args={[0.24, 0.04]} />
            <meshBasicMaterial color="#030712" transparent opacity={0.88} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.PlaneGeometry(0.24, 0.04)]} />
            <lineBasicMaterial color="#f59e0b" />
          </lineSegments>
          <Text
            position={[0, 0, 0.002]}
            fontSize={0.015}
            color="#fbbf24"
            anchorX="center"
            anchorY="middle"
          >
            {`Shoulder: ${shoulderCm} cm (${shoulderIn}")`}
          </Text>
        </Billboard>
      </group>

      {/* 3. BODY LENGTH (HPS TO HEM) OVERLAY */}
      <group position={[-0.30, 0, 0.04]}>
        <line>
          <bufferGeometry
            attach="geometry"
            {...new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(0, 0, 0),
              new THREE.Vector3(0, lengthM, 0),
            ])}
          />
          <lineBasicMaterial color="#10b981" linewidth={2} />
        </line>
        <mesh position={[0, lengthM, 0]}>
          <boxGeometry args={[0.025, 0.002, 0.002]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[0.025, 0.002, 0.002]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
        {/* Dynamic camera-facing Billboard badge */}
        <Billboard position={[-0.08, lengthM / 2, 0]}>
          <mesh>
            <planeGeometry args={[0.22, 0.04]} />
            <meshBasicMaterial color="#030712" transparent opacity={0.88} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.PlaneGeometry(0.22, 0.04)]} />
            <lineBasicMaterial color="#10b981" />
          </lineSegments>
          <Text
            position={[0, 0, 0.002]}
            fontSize={0.014}
            color="#34d399"
            anchorX="center"
            anchorY="middle"
          >
            {`Length: ${lengthCm} cm (${lengthIn}")`}
          </Text>
        </Billboard>
      </group>

      {/* 4. SLEEVE LENGTH OVERLAY */}
      <group position={[shoulderM / 2 + 0.02, zShoulderTip - 0.04, 0]}>
        <line>
          <bufferGeometry
            attach="geometry"
            {...new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(0, 0, 0),
              new THREE.Vector3(
                sleeveM * Math.cos((48 * Math.PI) / 180),
                -sleeveM * Math.sin((48 * Math.PI) / 180),
                0
              ),
            ])}
          />
          <lineBasicMaterial color="#ec4899" linewidth={2} />
        </line>
        {/* Dynamic camera-facing Billboard badge */}
        <Billboard position={[0.08, -0.06, 0.02]}>
          <mesh>
            <planeGeometry args={[0.18, 0.035]} />
            <meshBasicMaterial color="#030712" transparent opacity={0.88} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.PlaneGeometry(0.18, 0.035)]} />
            <lineBasicMaterial color="#ec4899" />
          </lineSegments>
          <Text
            position={[0, 0, 0.002]}
            fontSize={0.013}
            color="#f472b6"
            anchorX="center"
            anchorY="middle"
          >
            {`Sleeve: ${sleeveCm} cm`}
          </Text>
        </Billboard>
      </group>

      {/* 5. TORSO DEPTH OVERLAY */}
      <group position={[0.26, zUnderarm, 0]}>
        <line>
          <bufferGeometry
            attach="geometry"
            {...new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(0, 0, -0.095),
              new THREE.Vector3(0, 0, 0.095),
            ])}
          />
          <lineBasicMaterial color="#a855f7" linewidth={2} />
        </line>
        {/* Dynamic camera-facing Billboard badge */}
        <Billboard position={[0, 0.03, 0]}>
          <mesh>
            <planeGeometry args={[0.16, 0.035]} />
            <meshBasicMaterial color="#030712" transparent opacity={0.88} />
          </mesh>
          <lineSegments>
            <edgesGeometry args={[new THREE.PlaneGeometry(0.16, 0.035)]} />
            <lineBasicMaterial color="#a855f7" />
          </lineSegments>
          <Text
            position={[0, 0, 0.002]}
            fontSize={0.013}
            color="#c084fc"
            anchorX="center"
            anchorY="middle"
          >
            {`Depth: ${(chestM / 2.45 / 2 * 100 * 2).toFixed(1)} cm`}
          </Text>
        </Billboard>
      </group>
    </group>
  );
};
