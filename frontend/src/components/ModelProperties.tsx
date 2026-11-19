import React from 'react';
import { Layers, Download, FileJson } from 'lucide-react';
import { ModelMetadata, GarmentConfiguration } from '../types/garment';

interface ModelPropertiesProps {
  metadata: ModelMetadata | null;
  activeConfig: GarmentConfiguration;
  isGenerating: boolean;
  onDownloadGLB: () => void;
  onDownloadMetadata: () => void;
}

export const ModelProperties: React.FC<ModelPropertiesProps> = ({
  metadata,
  activeConfig,
  isGenerating,
  onDownloadGLB,
  onDownloadMetadata,
}) => {
  return (
    <div className="w-72 md:w-80 h-full bg-studio-900 border-l studio-border flex flex-col justify-between text-xs select-none">
      <div className="p-4 space-y-4">
        {/* Section Header */}
        <div className="flex items-center justify-between border-b studio-border pb-2.5">
          <div className="flex items-center space-x-1.5">
            <Layers className="w-4 h-4 text-blue-400" />
            <h2 className="font-bold text-xs uppercase tracking-wider text-white">Model Properties</h2>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold">
            Size {activeConfig.selected_size}
          </span>
        </div>

        {/* 3D Physical Mesh Geometry Metrics */}
        {metadata ? (
          <div className="p-3.5 rounded-lg bg-studio-950 border border-studio-800 space-y-3">
            <span className="text-[10px] font-mono uppercase text-studio-400 font-semibold block">
              Physical Mesh Geometry
            </span>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded bg-studio-900 border border-studio-800/80">
                <span className="text-[10px] text-studio-500 block">Width</span>
                <span className="font-mono font-bold text-studio-200">
                  {(metadata.dimensions.width_m * 100).toFixed(1)} cm
                </span>
              </div>
              <div className="p-2 rounded bg-studio-900 border border-studio-800/80">
                <span className="text-[10px] text-studio-500 block">Height</span>
                <span className="font-mono font-bold text-studio-200">
                  {(metadata.dimensions.height_m * 100).toFixed(1)} cm
                </span>
              </div>
              <div className="p-2 rounded bg-studio-900 border border-studio-800/80">
                <span className="text-[10px] text-studio-500 block">Depth</span>
                <span className="font-mono font-bold text-studio-200">
                  {(metadata.dimensions.depth_m * 100).toFixed(1)} cm
                </span>
              </div>
            </div>

            <div className="pt-2.5 border-t border-studio-850 grid grid-cols-2 gap-2 text-[11px] font-mono text-studio-400">
              <div className="flex items-center justify-between">
                <span>Vertices:</span>
                <span className="text-studio-200 font-semibold">{metadata.vertex_count.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Faces:</span>
                <span className="text-studio-200 font-semibold">{metadata.face_count.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Fabric Thick:</span>
                <span className="text-studio-200 font-semibold">1.8 mm</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Engine:</span>
                <span className="text-emerald-400 font-semibold">Blender 5.3</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-studio-950/60 border border-studio-800 text-center text-studio-500 italic">
            Physical 3D mesh properties will appear here after model generation.
          </div>
        )}
      </div>

      {/* Model Export Controls Footer */}
      <div className="p-4 bg-studio-950 border-t studio-border space-y-2">
        <span className="text-[10px] font-mono uppercase text-studio-400 font-semibold block">
          Export Standalone 3D Asset
        </span>

        <button
          onClick={onDownloadGLB}
          disabled={!metadata || isGenerating}
          className={`w-full py-2.5 px-3 rounded-lg font-bold text-xs flex items-center justify-center space-x-2 transition-all ${
            metadata && !isGenerating
              ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30 active:scale-[0.99]'
              : 'bg-studio-850 text-studio-600 border border-studio-800 cursor-not-allowed'
          }`}
        >
          <Download className="w-4 h-4" />
          <span>Download GLB (tshirt_{activeConfig.selected_size}.glb)</span>
        </button>

        <button
          onClick={onDownloadMetadata}
          disabled={!metadata}
          className="w-full py-1.5 px-3 rounded bg-studio-900 hover:bg-studio-850 border border-studio-800 text-studio-300 hover:text-white text-xs font-mono flex items-center justify-center space-x-1.5 transition-colors disabled:opacity-40"
        >
          <FileJson className="w-3.5 h-3.5 text-cyan-400" />
          <span>Export Metadata JSON</span>
        </button>
      </div>
    </div>
  );
};
