import React from 'react';
import { Layers, Download, Sparkles, CheckCircle2, RotateCcw } from 'lucide-react';

interface HeaderProps {
  currentStep: number;
  selectedSize: string;
  isGenerating: boolean;
  hasModel: boolean;
  onOpenComparison: () => void;
  onQuickExport: () => void;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  selectedSize,
  isGenerating,
  hasModel,
  onOpenComparison,
  onQuickExport,
  onReset
}) => {
  const steps = [
    { num: 1, label: 'Product Source' },
    { num: 2, label: 'Visual Analysis' },
    { num: 3, label: '3D Synthesis' },
    { num: 4, label: 'Inspect & Export' },
  ];

  return (
    <header className="h-14 bg-studio-900 border-b studio-border flex items-center justify-between px-4 z-20 select-none">
      {/* Brand & Title */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-sm tracking-wide text-white uppercase">3D Garment Studio</h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              AI E-Commerce to 3D
            </span>
          </div>
          <p className="text-[11px] text-studio-400">Flipkart Product URL to Standalone Textured 3D Garment</p>
        </div>
      </div>

      {/* Workflow Progress Steps */}
      <div className="hidden md:flex items-center space-x-2">
        {steps.map((s, idx) => {
          const isActive = currentStep === s.num;
          const isDone = currentStep > s.num;
          return (
            <React.Fragment key={s.num}>
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                isActive 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : isDone
                  ? 'text-emerald-400'
                  : 'text-studio-500'
              }`}>
                {isDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    isActive ? 'bg-blue-500 text-white font-bold' : 'bg-studio-800 text-studio-400'
                  }`}>
                    {s.num}
                  </span>
                )}
                <span>{s.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div className={`w-4 h-[1px] ${isDone ? 'bg-emerald-500/40' : 'bg-studio-800'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Quick Action Buttons */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onOpenComparison}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-studio-800 hover:bg-studio-750 text-studio-300 hover:text-white text-xs font-medium transition-colors border border-studio-700"
          title="Compare sizing across all sizes"
        >
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Size Matrix</span>
        </button>

        <button
          onClick={onQuickExport}
          disabled={!hasModel || isGenerating}
          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
            hasModel && !isGenerating
              ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30'
              : 'bg-studio-800 text-studio-500 cursor-not-allowed border border-studio-750'
          }`}
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export GLB ({selectedSize})</span>
        </button>

        <button
          onClick={onReset}
          className="p-1.5 rounded-md bg-studio-800 hover:bg-studio-750 text-studio-400 hover:text-white transition-colors"
          title="Start new project"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
