import React from 'react';
import { SizeChartData } from '../types/measurements';
import { CheckCircle2, Sparkles } from 'lucide-react';

interface SizeSelectorProps {
  sizes: string[];
  selectedSize: string;
  onSelectSize: (size: string) => void;
  chartData: SizeChartData | null;
  generatedSizes?: string[];
  isGenerating?: boolean;
}

export const SizeSelector: React.FC<SizeSelectorProps> = ({
  sizes,
  selectedSize,
  onSelectSize,
  chartData,
  generatedSizes = [],
  isGenerating = false,
}) => {
  const standardSizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const displaySizes = standardSizes.filter((s) => sizes.includes(s));
  const effectiveSizes = displaySizes.length > 0 ? displaySizes : sizes;

  if (effectiveSizes.length === 0) return null;

  const activeMeasurements = chartData?.sizes[selectedSize];
  const unit = chartData?.unit || 'cm';

  return (
    <div className="space-y-2 pt-2 border-t studio-border">
      <div className="flex items-center justify-between text-xs">
        <label className="font-semibold text-studio-300 uppercase tracking-wider text-[11px] flex items-center space-x-1">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>Select Size</span>
        </label>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-studio-800 text-studio-300 border border-studio-700">
          Selected: <strong className="text-white font-bold">{selectedSize}</strong>
        </span>
      </div>

      {/* S | M | L | XL | XXL Button Grid */}
      <div className="grid grid-cols-5 gap-1.5 bg-studio-950 p-1 rounded-lg border border-studio-800">
        {effectiveSizes.map((sz) => {
          const isSelected = sz === selectedSize;
          const isGenerated = generatedSizes.includes(sz);

          return (
            <button
              key={sz}
              onClick={() => onSelectSize(sz)}
              disabled={isGenerating}
              className={`py-2 px-1 text-xs font-mono font-bold rounded flex flex-col items-center justify-center transition-all ${
                isSelected
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 ring-1 ring-blue-400 scale-[1.02]'
                  : 'text-studio-400 hover:text-studio-200 hover:bg-studio-850'
              } ${isGenerating ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              <span>{sz}</span>
              {isGenerated && (
                <span className={`text-[9px] mt-0.5 ${isSelected ? 'text-blue-200' : 'text-emerald-400'}`}>
                  3D Ready
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Extracted Measurement Summary for Selected Size */}
      {activeMeasurements && (
        <div className="p-2 rounded bg-studio-900/80 border border-studio-800 text-[11px] font-mono text-studio-300 flex flex-wrap gap-x-3 gap-y-1 justify-between">
          <span>Chest: <strong className="text-white">{activeMeasurements.chest} {unit}</strong></span>
          <span>Shoulder: <strong className="text-white">{activeMeasurements.shoulder} {unit}</strong></span>
          <span>Length: <strong className="text-white">{activeMeasurements.length} {unit}</strong></span>
          <span>Sleeve: <strong className="text-white">{activeMeasurements.sleeve} {unit}</strong></span>
        </div>
      )}
    </div>
  );
};
