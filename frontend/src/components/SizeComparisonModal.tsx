import React from 'react';
import { X, Sparkles, Check, ArrowRight, Layers, Ruler } from 'lucide-react';
import { SizeChartData } from '../types/measurements';

interface SizeComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  chartData: SizeChartData | null;
  selectedSize: string;
  onSelectSize: (size: string) => void;
  onGenerateSize: (size: string) => void;
  generatedSizes: Record<string, string>; // size -> model_url
}

export const SizeComparisonModal: React.FC<SizeComparisonModalProps> = ({
  isOpen,
  onClose,
  chartData,
  selectedSize,
  onSelectSize,
  onGenerateSize,
  generatedSizes,
}) => {
  if (!isOpen || !chartData) return null;

  const sizes = Object.keys(chartData.sizes);
  const baseMeasurements = chartData.sizes[selectedSize];

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 select-none">
      <div className="bg-studio-900 border border-studio-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b studio-border flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white uppercase tracking-wider">Garment Size Comparison Matrix</h3>
              <p className="text-[11px] text-studio-400">
                Parametric grading & dimensional variation across all sizes (Base size: {selectedSize})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-studio-800 text-studio-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Table */}
        <div className="p-4 overflow-y-auto space-y-4">
          <div className="border border-studio-800 rounded-lg overflow-x-auto bg-studio-950/70">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-studio-800 bg-studio-900/90 text-[11px] font-mono text-studio-400">
                  <th className="p-3 font-semibold text-studio-300">Size Spec</th>
                  {sizes.map((sz) => {
                    const isSelected = sz === selectedSize;
                    const isGenerated = !!generatedSizes[sz];
                    return (
                      <th
                        key={sz}
                        className={`p-3 text-center ${
                          isSelected ? 'bg-blue-600/20 text-blue-300 font-bold border-b-2 border-blue-500' : ''
                        }`}
                      >
                        <div className="flex flex-col items-center space-y-1">
                          <span className="text-sm font-bold">{sz}</span>
                          {isGenerated ? (
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                              3D Ready
                            </span>
                          ) : (
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-studio-800 text-studio-500">
                              Unbuilt
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-studio-850 font-mono text-xs">
                {/* Chest */}
                <tr className="hover:bg-studio-900/30">
                  <td className="p-3 font-sans font-medium text-studio-300">Chest Circumference</td>
                  {sizes.map((sz) => {
                    const val = chartData.sizes[sz]?.chest || 0;
                    const diff = baseMeasurements ? val - baseMeasurements.chest : 0;
                    return (
                      <td key={sz} className="p-3 text-center">
                        <span className="font-semibold text-white">{val} {chartData.unit}</span>
                        {sz !== selectedSize && diff !== 0 && (
                          <span className={`block text-[10px] ${diff > 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                            {diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* Shoulder */}
                <tr className="hover:bg-studio-900/30">
                  <td className="p-3 font-sans font-medium text-studio-300">Shoulder Width</td>
                  {sizes.map((sz) => {
                    const val = chartData.sizes[sz]?.shoulder || 0;
                    const diff = baseMeasurements ? val - baseMeasurements.shoulder : 0;
                    return (
                      <td key={sz} className="p-3 text-center">
                        <span className="font-semibold text-white">{val} {chartData.unit}</span>
                        {sz !== selectedSize && diff !== 0 && (
                          <span className={`block text-[10px] ${diff > 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                            {diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* Length */}
                <tr className="hover:bg-studio-900/30">
                  <td className="p-3 font-sans font-medium text-studio-300">Garment Length</td>
                  {sizes.map((sz) => {
                    const val = chartData.sizes[sz]?.length || 0;
                    const diff = baseMeasurements ? val - baseMeasurements.length : 0;
                    return (
                      <td key={sz} className="p-3 text-center">
                        <span className="font-semibold text-white">{val} {chartData.unit}</span>
                        {sz !== selectedSize && diff !== 0 && (
                          <span className={`block text-[10px] ${diff > 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                            {diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* Sleeve */}
                <tr className="hover:bg-studio-900/30">
                  <td className="p-3 font-sans font-medium text-studio-300">Sleeve Length</td>
                  {sizes.map((sz) => {
                    const val = chartData.sizes[sz]?.sleeve || 0;
                    const diff = baseMeasurements && baseMeasurements.sleeve !== null && baseMeasurements.sleeve !== undefined
                      ? val - baseMeasurements.sleeve
                      : 0;
                    return (
                      <td key={sz} className="p-3 text-center">
                        <span className="font-semibold text-white">{val} {chartData.unit}</span>
                        {sz !== selectedSize && diff !== 0 && (
                          <span className={`block text-[10px] ${diff > 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                            {diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>

                {/* Action Row */}
                <tr className="bg-studio-900/50">
                  <td className="p-3 font-sans font-semibold text-studio-400">Viewport Actions</td>
                  {sizes.map((sz) => {
                    const isSelected = sz === selectedSize;
                    const isGenerated = !!generatedSizes[sz];
                    return (
                      <td key={sz} className="p-3 text-center">
                        {isSelected ? (
                          <span className="text-[11px] font-bold text-blue-400 flex items-center justify-center space-x-1">
                            <Check className="w-3.5 h-3.5" />
                            <span>Active In 3D</span>
                          </span>
                        ) : (
                          <div className="flex flex-col items-center space-y-1">
                            <button
                              onClick={() => {
                                onSelectSize(sz);
                                onClose();
                              }}
                              className="px-2.5 py-1 rounded bg-studio-800 hover:bg-studio-700 text-studio-200 text-[11px] font-sans font-medium transition-colors w-full"
                            >
                              Select {sz}
                            </button>
                            {!isGenerated && (
                              <button
                                onClick={() => {
                                  onGenerateSize(sz);
                                  onClose();
                                }}
                                className="text-[10px] text-cyan-400 hover:underline flex items-center space-x-0.5"
                              >
                                <Sparkles className="w-2.5 h-2.5" />
                                <span>Generate</span>
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>

          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
            <p className="font-semibold">Independent Parametric Geometry Formulation:</p>
            <p className="text-[11px] text-studio-300 mt-0.5">
              Each size is constructed from individual mathematical cross-sections and Ramanujan ellipse circumferences
              rather than uniform model scaling, preserving correct fabric draping proportions across the size range.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
