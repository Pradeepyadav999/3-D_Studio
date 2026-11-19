import React from 'react';
import { Sliders, Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { FitType, SleeveType, NeckType } from '../types/garment';

interface GarmentSettingsProps {
  fit: FitType;
  sleeveType: SleeveType;
  neckType: NeckType;
  onFitChange: (fit: FitType) => void;
  onSleeveTypeChange: (sleeve: SleeveType) => void;
  onNeckTypeChange: (neck: NeckType) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  canGenerate: boolean;
  selectedSize: string;
  hasInvalidMeasurement?: boolean;
}

export const GarmentSettings: React.FC<GarmentSettingsProps> = ({
  fit,
  sleeveType,
  neckType,
  onFitChange,
  onSleeveTypeChange,
  onNeckTypeChange,
  onGenerate,
  isGenerating,
  canGenerate,
  selectedSize,
  hasInvalidMeasurement = false,
}) => {
  return (
    <div className="space-y-3 pt-2 border-t studio-border">
      <div className="flex items-center space-x-1.5 text-xs font-semibold uppercase tracking-wider text-studio-300">
        <Sliders className="w-3.5 h-3.5 text-blue-400" />
        <span>Garment Specifications</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        {/* Fit Silhouette */}
        <div>
          <label className="text-[10px] text-studio-400 block mb-1 uppercase font-mono">Fit Silhouette</label>
          <select
            value={fit}
            onChange={(e) => onFitChange(e.target.value as FitType)}
            className="w-full bg-studio-900 border border-studio-800 rounded px-2 py-1.5 text-studio-200 text-xs focus:outline-none focus:border-blue-500 font-medium"
          >
            <option value="regular">Regular Fit</option>
            <option value="slim">Slim Fit</option>
            <option value="relaxed">Relaxed Fit</option>
          </select>
        </div>

        {/* Sleeve Type */}
        <div>
          <label className="text-[10px] text-studio-400 block mb-1 uppercase font-mono">Sleeve Cut</label>
          <select
            value={sleeveType}
            onChange={(e) => onSleeveTypeChange(e.target.value as SleeveType)}
            className="w-full bg-studio-900 border border-studio-800 rounded px-2 py-1.5 text-studio-200 text-xs focus:outline-none focus:border-blue-500 font-medium"
          >
            <option value="short">Short Sleeve</option>
            <option value="long">Long Sleeve</option>
          </select>
        </div>

        {/* Neckline */}
        <div>
          <label className="text-[10px] text-studio-400 block mb-1 uppercase font-mono">Neckline</label>
          <select
            value={neckType}
            onChange={(e) => onNeckTypeChange(e.target.value as NeckType)}
            className="w-full bg-studio-900 border border-studio-800 rounded px-2 py-1.5 text-studio-200 text-xs focus:outline-none focus:border-blue-500 font-medium"
          >
            <option value="round">Round Neck</option>
            <option value="v_neck">V-Neck</option>
          </select>
        </div>
      </div>

      {/* Validation Alert if required measurements are zero or missing */}
      {hasInvalidMeasurement && (
        <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Cannot generate: Missing or 0 measurement for Size {selectedSize}.</span>
        </div>
      )}

      {/* Primary 3D Generation Action Button */}
      <button
        onClick={onGenerate}
        disabled={!canGenerate || isGenerating || hasInvalidMeasurement}
        className={`w-full py-2.5 px-4 rounded-lg font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-lg ${
          canGenerate && !isGenerating && !hasInvalidMeasurement
            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/25 active:scale-[0.99]'
            : 'bg-studio-800 text-studio-500 border border-studio-750 cursor-not-allowed'
        }`}
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-white" />
            <span>Calculating 3D Mesh in Blender...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span>Generate 3D Model ({selectedSize})</span>
          </>
        )}
      </button>
    </div>
  );
};
