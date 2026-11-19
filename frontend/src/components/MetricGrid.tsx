import React, { useMemo } from 'react';
import * as THREE from 'three';
import { Text, Billboard } from '@react-three/drei';

interface MetricGridProps {
  visible?: boolean;
  isValidationMode?: boolean;
}

export const MetricGrid: React.FC<MetricGridProps> = ({
  visible = true,
  isValidationMode = false,
}) => {
  if (!visible) return null;

  // 1. Clean Subtle Floor Grid for Normal Mode (10cm divisions, non-intrusive)
  const normalGridGeo = useMemo(() => {
    const pts: number[] = [];
    const extent = 0.80; // 80 cm in each direction
    const step = 0.10; // 10 cm grid spacing
    for (let x = -extent; x <= extent + 1e-5; x += step) {
      pts.push(x, 0, -extent, x, 0, extent);
    }
    for (let z = -extent; z <= extent + 1e-5; z += step) {
      pts.push(-extent, 0, z, extent, 0, z);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    return geo;
  }, []);

  // 2. High-Precision Calibrated 1cm Minor / 10cm Major Grid for Validation Mode
  const { minorLinesGeo, majorLinesGeo, axisLinesGeo } = useMemo(() => {
    const minorPts: number[] = [];
    const majorPts: number[] = [];
    const axisPts: number[] = [];

    const extent = 0.80; // 80 cm
    const minorStep = 0.01; // 1 cm
    const majorStep = 0.10; // 10 cm

    for (let x = -extent; x <= extent + 1e-5; x += minorStep) {
      const isMajor = Math.abs(Math.round(x / majorStep) * majorStep - x) < 1e-4;
      const isAxis = Math.abs(x) < 1e-4;
      if (isAxis) {
        axisPts.push(0, 0, -extent, 0, 0, extent);
      } else if (isMajor) {
        majorPts.push(x, 0, -extent, x, 0, extent);
      } else {
        minorPts.push(x, 0, -extent, x, 0, extent);
      }
    }

    for (let z = -extent; z <= extent + 1e-5; z += minorStep) {
      const isMajor = Math.abs(Math.round(z / majorStep) * majorStep - z) < 1e-4;
      const isAxis = Math.abs(z) < 1e-4;
      if (isAxis) {
        axisPts.push(-extent, 0, 0, extent, 0, 0);
      } else if (isMajor) {
        majorPts.push(-extent, 0, z, extent, 0, z);
      } else {
        minorPts.push(-extent, 0, z, extent, 0, z);
      }
    }

    const minor = new THREE.BufferGeometry();
    minor.setAttribute('position', new THREE.Float32BufferAttribute(minorPts, 3));

    const major = new THREE.BufferGeometry();
    major.setAttribute('position', new THREE.Float32BufferAttribute(majorPts, 3));

    const axis = new THREE.BufferGeometry();
    axis.setAttribute('position', new THREE.Float32BufferAttribute(axisPts, 3));

    return { minorLinesGeo: minor, majorLinesGeo: major, axisLinesGeo: axis };
  }, []);

  // 3. Vertical Height Ruler Ticks (0cm to 80cm)
  const verticalRulerTicks = useMemo(() => {
    const ticks: { y: number; isMajor: boolean; label?: string }[] = [];
    for (let y = 0; y <= 0.80 + 1e-4; y += 0.01) {
      const cm = Math.round(y * 100);
      const isMajor = cm % 10 === 0;
      ticks.push({
        y,
        isMajor,
        label: isMajor ? `${cm} cm` : undefined,
      });
    }
    return ticks;
  }, []);

  // A. NORMAL MODE: Clean, subtle dark floor grid without any numbers, rulers or calibration cubes
  if (!isValidationMode) {
    return (
      <group position={[0, 0, 0]}>
        <lineSegments geometry={normalGridGeo}>
          <lineBasicMaterial color="#1a202c" transparent opacity={0.5} depthWrite={false} />
        </lineSegments>
      </group>
    );
  }

  // B. DIMENSION VALIDATION MODE: Calibrated metric grid, billboard rulers, and reference cube
  return (
    <group position={[0, 0, 0]}>
      {/* Minor 1cm grid lines */}
      <lineSegments geometry={minorLinesGeo}>
        <lineBasicMaterial color="#172033" transparent opacity={0.65} depthWrite={false} />
      </lineSegments>

      {/* Major 10cm grid lines */}
      <lineSegments geometry={majorLinesGeo}>
        <lineBasicMaterial color="#2d3748" transparent opacity={0.85} depthWrite={false} />
      </lineSegments>

      {/* Axis Lines (X in red, Z in blue) */}
      <lineSegments geometry={axisLinesGeo}>
        <lineBasicMaterial color="#0284c7" depthWrite={false} />
      </lineSegments>

      {/* Origin Ring Indicator */}
      <mesh position={[0, 0.001, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.006, 0.012, 32]} />
        <meshBasicMaterial color="#00f0ff" side={THREE.DoubleSide} />
      </mesh>

      {/* 10 x 10 x 10 cm Reference Cube */}
      <group position={[0.38, 0.05, 0.22]}>
        <mesh castShadow receiveShadow>
          <boxGeometry args={[0.10, 0.10, 0.10]} />
          <meshStandardMaterial
            color="#0284c7"
            transparent
            opacity={0.30}
            roughness={0.2}
            metalness={0.1}
          />
        </mesh>
        <lineSegments>
          <edgesGeometry args={[new THREE.BoxGeometry(0.10, 0.10, 0.10)]} />
          <lineBasicMaterial color="#38bdf8" />
        </lineSegments>
        {/* Dynamic camera-facing Billboard label */}
        <Billboard position={[0, 0.08, 0]}>
          <Text
            fontSize={0.016}
            color="#38bdf8"
            anchorX="center"
            anchorY="middle"
          >
            10×10×10 cm Cube
          </Text>
        </Billboard>
      </group>

      {/* Vertical Height Ruler positioned safely alongside garment at X = -0.48m */}
      <group position={[-0.48, 0, 0]}>
        {/* Vertical Spine */}
        <mesh position={[0, 0.40, 0]}>
          <boxGeometry args={[0.002, 0.80, 0.002]} />
          <meshBasicMaterial color="#0ea5e9" />
        </mesh>

        {/* Ticks and camera-facing text labels */}
        {verticalRulerTicks.map((tick, i) => {
          const tickLen = tick.isMajor ? 0.020 : 0.008;
          return (
            <group key={`vtick-${i}`} position={[0, tick.y, 0]}>
              <mesh position={[tickLen / 2, 0, 0]}>
                <boxGeometry args={[tickLen, 0.0012, 0.002]} />
                <meshBasicMaterial color={tick.isMajor ? '#38bdf8' : '#475569'} />
              </mesh>
              {tick.label && (
                <Billboard position={[-0.018, 0, 0]}>
                  <Text
                    fontSize={0.015}
                    color="#f8fafc"
                    anchorX="right"
                    anchorY="middle"
                  >
                    {tick.label}
                  </Text>
                </Billboard>
              )}
            </group>
          );
        })}
      </group>
    </group>
  );
};
