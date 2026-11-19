import React from 'react';
import { 
  RotateCcw, Maximize, Grid, Box, Compass, Sparkles, Layers, Eye, Ruler, ShieldCheck
} from 'lucide-react';
import { ShadingMode, ViewPreset } from '../types/garment';

interface ViewportToolbarProps {
  shadingMode: ShadingMode;
  onShadingModeChange: (mode: ShadingMode) => void;
  viewPreset: ViewPreset;
  onViewPresetChange: (view: ViewPreset) => void;
  onResetCamera: () => void;
  onFitModel: () => void;
  showGrid: boolean;
  onToggleGrid: () => void;
  showBoundingBox: boolean;
  onToggleBoundingBox: () => void;
  showDimensions?: boolean;
  onToggleDimensions?: () => void;
  onOpenAccuracyReport?: () => void;
  hasModel: boolean;
  hasTexture?: boolean;
}

export const ViewportToolbar: React.FC<ViewportToolbarProps> = ({
  shadingMode,
  onShadingModeChange,
  viewPreset,
  onViewPresetChange,
  onResetCamera,
  onFitModel,
  showGrid,
  onToggleGrid,
  showBoundingBox,
  onToggleBoundingBox,
  showDimensions = false,
  onToggleDimensions,
  onOpenAccuracyReport,
  hasModel,
  hasTexture = true,
}) => {
  const modes: { id: ShadingMode; label: string; icon: React.ReactNode; tooltip: string }[] = [
    { 
      id: 'textured', 
      label: 'TEXTURED', 
      icon: <Sparkles className="w-3.5 h-3.5" />, 
      tooltip: 'Original Flipkart product appearance with authentic artwork & graphics' 
    },
    { 
      id: 'solid', 
      label: 'SOLID', 
      icon: <Box className="w-3.5 h-3.5" />, 
      tooltip: 'Neutral solid material for inspecting garment shape & proportions' 
    },
    { 
      id: 'wireframe', 
      label: 'WIRE', 
      icon: <Eye className="w-3.5 h-3.5" />, 
      tooltip: 'Actual garment mesh polygon edges & topology' 
    },
    { 
      id: 'solid_wireframe', 
      label: 'SOLID + WIRE', 
      icon: <Layers className="w-3.5 h-3.5" />, 
      tooltip: 'Solid garment surface with polygon wireframe overlay' 
    },
  ];

  const cameraViews: { id: ViewPreset; label: string }[] = [
    { id: 'perspective', label: 'Perspective' },
    { id: 'front', label: 'Front' },
    { id: 'back', label: 'Back' },
    { id: 'left', label: 'Left' },
    { id: 'right', label: 'Right' },
    { id: 'top', label: 'Top' },
  ];

  return (
    <div className="w-full bg-studio-900 border-b border-studio-800 px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 z-10 flex-shrink-0 select-none shadow-md">
      {/* 1. VIEW MODE BUTTONS (TEXTURED, SOLID, WIRE, SOLID + WIRE) */}
      <div className="flex items-center space-x-1 bg-studio-950 p-1 rounded-lg border border-studio-800">
        <span className="text-[10px] font-mono uppercase tracking-wider text-studio-400 font-bold px-1.5 mr-0.5">
          Mode:
        </span>
        {modes.map((m) => {
          const isActive = shadingMode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onShadingModeChange(m.id)}
              className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono font-bold rounded-md transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md ring-1 ring-blue-400/50'
                  : 'text-studio-300 hover:text-white hover:bg-studio-800/80'
              }`}
              title={m.tooltip}
            >
              <span className={isActive ? 'text-white' : 'text-studio-400'}>{m.icon}</span>
              <span>{m.label}</span>
              {m.id === 'textured' && hasTexture && (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 ml-0.5" title="Texture Active" />
              )}
            </button>
          );
        })}
      </div>

      {/* 2. CAMERA CONTROLS (Perspective, Front, Back, Left, Right, Top) */}
      <div className="flex items-center space-x-1 bg-studio-950 p-1 rounded-lg border border-studio-800">
        <div className="flex items-center px-1 text-studio-400">
          <Compass className="w-3.5 h-3.5 text-cyan-400 mr-1" />
          <span className="text-[10px] font-mono uppercase font-bold text-studio-300">Camera:</span>
        </div>
        {cameraViews.map((v) => {
          const isActive = viewPreset === v.id;
          return (
            <button
              key={v.id}
              type="button"
              onClick={() => onViewPresetChange(v.id)}
              className={`px-2 py-1 text-[11px] font-mono rounded font-medium transition-all ${
                isActive
                  ? 'bg-studio-800 text-blue-400 font-bold border border-studio-700 shadow-sm'
                  : 'text-studio-400 hover:text-white hover:bg-studio-850'
              }`}
            >
              {v.label}
            </button>
          );
        })}
      </div>

      {/* 3. VIEWPORT UTILITIES & INSPECTION HELPERS */}
      <div className="flex items-center space-x-1">
        {/* Toggle Bounding Box */}
        <button
          type="button"
          onClick={onToggleBoundingBox}
          className={`p-1.5 rounded-lg border transition-colors ${
            showBoundingBox
              ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
              : 'bg-studio-950 border-studio-800 text-studio-400 hover:text-white hover:bg-studio-850'
          }`}
          title="Toggle 3D Bounding Box & Dimensions"
        >
          <Box className="w-3.5 h-3.5" />
        </button>

        {/* Toggle Dimension Validation Mode */}
        {onToggleDimensions && (
          <button
            type="button"
            onClick={onToggleDimensions}
            className={`p-1.5 rounded-lg border transition-all flex items-center gap-1.5 ${
              showDimensions
                ? 'bg-amber-500/20 text-amber-300 border-amber-400/60 shadow-md ring-1 ring-amber-400/30'
                : 'bg-studio-950 border-studio-800 text-studio-400 hover:text-white hover:bg-studio-850'
            }`}
            title={
              showDimensions
                ? 'Switch to Normal Product View (Clean hero preview without measurement clutter)'
                : 'Switch to Dimension Validation Mode (Show calibrated metric grid, rulers & 3D measurements)'
            }
          >
            <Ruler className="w-3.5 h-3.5" />
            <span className="text-[10px] font-mono font-bold hidden sm:inline">
              {showDimensions ? 'VALIDATION: ON' : 'VALIDATION'}
            </span>
          </button>
        )}

        {/* View Measurement Accuracy Report */}
        {onOpenAccuracyReport && (
          <button
            type="button"
            onClick={onOpenAccuracyReport}
            className="p-1.5 rounded-lg border bg-studio-950 border-emerald-500/40 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/40 transition-colors flex items-center gap-1"
            title="View Calibrated Measurement Accuracy Audit (Pass/Fail Report)"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[10px] font-mono font-bold text-emerald-400 hidden sm:inline">ACCURACY</span>
          </button>
        )}

        {/* Toggle Floor Grid */}
        <button
          type="button"
          onClick={onToggleGrid}
          className={`p-1.5 rounded-lg border transition-colors ${
            showGrid
              ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
              : 'bg-studio-950 border-studio-800 text-studio-400 hover:text-white hover:bg-studio-850'
          }`}
          title="Toggle Floor Grid"
        >
          <Grid className="w-3.5 h-3.5" />
        </button>

        <div className="h-4 w-[1px] bg-studio-800 mx-0.5" />

        {/* Fit to Viewport */}
        <button
          type="button"
          onClick={onFitModel}
          disabled={!hasModel}
          className="p-1.5 rounded-lg bg-studio-950 border border-studio-800 text-studio-400 hover:text-white hover:bg-studio-850 disabled:opacity-40 transition-colors"
          title="Fit Model to Viewport"
        >
          <Maximize className="w-3.5 h-3.5" />
        </button>

        {/* Reset Camera */}
        <button
          type="button"
          onClick={onResetCamera}
          className="p-1.5 rounded-lg bg-studio-950 border border-studio-800 text-studio-400 hover:text-white hover:bg-studio-850 transition-colors"
          title="Reset Camera"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
