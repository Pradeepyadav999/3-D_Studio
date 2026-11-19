import React, { useState } from 'react';
import { Eye, AlertTriangle, CheckCircle, FileCode, ChevronDown, ChevronUp } from 'lucide-react';
import { SizeChartData } from '../types/measurements';

interface SizeChartPreviewProps {
  chartData: SizeChartData | null;
  fileUrl: string | null;
}

export const SizeChartPreview: React.FC<SizeChartPreviewProps> = ({ chartData, fileUrl }) => {
  const [showRawOcr, setShowRawOcr] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);

  if (!chartData && !fileUrl) return null;

  return (
    <div className="space-y-2 pt-2 border-t studio-border">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-studio-300">Extraction Summary</span>
        {chartData && (
          <div className="flex items-center space-x-1.5">
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
              chartData.confidence >= 0.8
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              OCR: {Math.round(chartData.confidence * 100)}% Conf.
            </span>
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
              chartData.measurement_type === 'garment'
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              {chartData.measurement_type.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Image Preview thumbnail with click to enlarge */}
      {fileUrl && (
        <div
          onClick={() => setShowImageModal(true)}
          className="relative group rounded-md overflow-hidden border border-studio-750 bg-studio-900 cursor-pointer h-24 flex items-center justify-center"
        >
          <img
            src={fileUrl}
            alt="Size chart preview"
            className="w-full h-full object-contain p-1 transition-transform group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-1 text-white text-xs font-medium">
            <Eye className="w-4 h-4" />
            <span>Enlarge Chart</span>
          </div>
        </div>
      )}

      {/* Warnings if any */}
      {chartData?.warnings && chartData.warnings.length > 0 && (
        <div className="space-y-1">
          {chartData.warnings.map((w, idx) => (
            <div
              key={idx}
              className="flex items-start space-x-1.5 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]"
            >
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-amber-400" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Raw OCR Text toggle */}
      {chartData?.raw_ocr_text && (
        <div>
          <button
            onClick={() => setShowRawOcr(!showRawOcr)}
            className="flex items-center space-x-1 text-[11px] text-studio-400 hover:text-studio-200 transition-colors"
          >
            <FileCode className="w-3 h-3" />
            <span>Raw OCR Transcript</span>
            {showRawOcr ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {showRawOcr && (
            <pre className="mt-1.5 p-2 rounded bg-studio-950 border border-studio-800 text-[10px] font-mono text-studio-300 overflow-x-auto max-h-28 whitespace-pre-wrap">
              {chartData.raw_ocr_text}
            </pre>
          )}
        </div>
      )}

      {/* Enlarge Image Modal */}
      {showImageModal && fileUrl && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setShowImageModal(false)}
        >
          <div className="relative max-w-4xl max-h-[85vh] bg-studio-900 border border-studio-700 rounded-lg p-2 shadow-2xl">
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute top-3 right-3 px-2 py-1 bg-studio-800 text-studio-300 hover:text-white rounded text-xs"
            >
              Close
            </button>
            <img src={fileUrl} alt="Size chart full" className="max-h-[80vh] object-contain rounded" />
          </div>
        </div>
      )}
    </div>
  );
};
