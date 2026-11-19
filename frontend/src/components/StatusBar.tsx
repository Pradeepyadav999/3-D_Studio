import React from 'react';
import { Cpu, Box, CheckCircle, Activity, Disc } from 'lucide-react';
import { ModelMetadata } from '../types/garment';

interface StatusBarProps {
  selectedSize: string;
  isGenerating: boolean;
  metadata: ModelMetadata | null;
  shadingMode: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  selectedSize,
  isGenerating,
  metadata,
  shadingMode,
}) => {
  return (
    <footer className="h-7 bg-studio-950 border-t studio-border px-3 flex items-center justify-between text-[11px] font-mono text-studio-400 select-none">
      {/* Left: Engine & Worker Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1.5">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span>Blender Worker:</span>
          {isGenerating ? (
            <span className="flex items-center space-x-1 text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              <span>Generating Geometry...</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Active (v5.3.0)</span>
            </span>
          )}
        </div>

        <div className="h-3 w-[1px] bg-studio-800" />

        <div className="flex items-center space-x-1">
          <span className="text-studio-500">Active Size:</span>
          <span className="font-bold text-studio-200 px-1 rounded bg-studio-800">{selectedSize}</span>
        </div>

        <div className="h-3 w-[1px] bg-studio-800" />

        <div className="flex items-center space-x-1">
          <span className="text-studio-500">Shading:</span>
          <span className="text-studio-300 capitalize">{shadingMode.replace('_', ' + ')}</span>
        </div>
      </div>

      {/* Right: Model Polygon / Geometry Stats */}
      <div className="flex items-center space-x-4">
        {metadata ? (
          <>
            <div className="flex items-center space-x-1.5">
              <Box className="w-3.5 h-3.5 text-studio-500" />
              <span className="text-studio-500">Vertices:</span>
              <span className="text-studio-200">{metadata.vertex_count.toLocaleString()}</span>
            </div>

            <div className="h-3 w-[1px] bg-studio-800" />

            <div className="flex items-center space-x-1.5">
              <Disc className="w-3.5 h-3.5 text-studio-500" />
              <span className="text-studio-500">Faces:</span>
              <span className="text-studio-200">{metadata.face_count.toLocaleString()}</span>
            </div>

            <div className="h-3 w-[1px] bg-studio-800" />

            <div className="flex items-center space-x-1.5 text-studio-400">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>
                {(metadata.dimensions.width_m * 100).toFixed(1)} x {(metadata.dimensions.height_m * 100).toFixed(1)} x {(metadata.dimensions.depth_m * 100).toFixed(1)} cm
              </span>
            </div>
          </>
        ) : (
          <span className="text-studio-500 italic">No model loaded</span>
        )}
      </div>
    </footer>
  );
};
