import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Image as ImageIcon, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { UploadResponse } from '../types/measurements';

interface FileUploadProps {
  onFileUploaded: (file: File, uploadData: UploadResponse) => void;
  onExtractRequested: (chartId: string) => void;
  isUploading: boolean;
  isExtracting: boolean;
  uploadedChart: UploadResponse | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileUploaded,
  onExtractRequested,
  isUploading,
  isExtracting,
  uploadedChart,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragover' || e.type === 'dragenter') {
      setIsDragOver(true);
    } else if (e.type === 'dragleave') {
      setIsDragOver(false);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    const validExts = ['png', 'jpg', 'jpeg', 'pdf'];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!validExts.includes(ext)) {
      setError('Please upload a valid PNG, JPG, or PDF size chart.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/size-chart/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        throw new Error('Upload failed');
      }
      const data: UploadResponse = await res.json();
      onFileUploaded(file, data);
    } catch (err: any) {
      setError(err.message || 'Failed to upload chart');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  // Load sample size chart directly from server
  const loadSampleChart = async () => {
    setError(null);
    try {
      const sampleRes = await fetch('/storage/sample_size_chart.png');
      const blob = await sampleRes.blob();
      const file = new File([blob], 'mens_tshirt_size_chart.png', { type: 'image/png' });
      await processFile(file);
    } catch {
      // If direct static fetch fails, fetch from api file endpoint
      const res = await fetch('/api/size-chart/file/sample_chart.png');
      const blob = await res.blob();
      const file = new File([blob], 'mens_tshirt_size_chart.png', { type: 'image/png' });
      await processFile(file);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-studio-300">Size Chart Input</h3>
        <button
          onClick={loadSampleChart}
          disabled={isUploading || isExtracting}
          className="flex items-center space-x-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
        >
          <Sparkles className="w-3 h-3" />
          <span>Load Sample Chart</span>
        </button>
      </div>

      {/* Drag & Drop Box */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-all ${
          isDragOver
            ? 'border-blue-500 bg-blue-500/10'
            : uploadedChart
            ? 'border-studio-700 bg-studio-900/60 hover:border-studio-600'
            : 'border-studio-750 bg-studio-900/40 hover:border-blue-500/50 hover:bg-studio-900/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.pdf"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="py-4 flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
            <p className="text-xs text-studio-300">Uploading size chart...</p>
          </div>
        ) : uploadedChart ? (
          <div className="flex items-center space-x-3 text-left">
            <div className="w-10 h-10 rounded bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
              {uploadedChart.content_type.includes('pdf') ? (
                <FileText className="w-5 h-5 text-rose-400" />
              ) : (
                <ImageIcon className="w-5 h-5 text-blue-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-studio-100 truncate">{uploadedChart.filename}</p>
              <p className="text-[10px] text-studio-400 font-mono">
                {(uploadedChart.size_bytes / 1024).toFixed(1)} KB • Click to replace
              </p>
            </div>
          </div>
        ) : (
          <div className="py-2 flex flex-col items-center justify-center space-y-2">
            <div className="w-9 h-9 rounded-full bg-studio-800 flex items-center justify-center text-studio-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-studio-200">
                <span className="text-blue-400">Click to upload</span> or drag & drop
              </p>
              <p className="text-[11px] text-studio-500 mt-0.5">PNG, JPG, JPEG, or PDF</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center space-x-2 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Extract Button */}
      {uploadedChart && (
        <button
          onClick={() => onExtractRequested(uploadedChart.chart_id)}
          disabled={isExtracting}
          className={`w-full py-2 px-3 rounded-md text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
            isExtracting
              ? 'bg-studio-800 text-studio-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-600/20'
          }`}
        >
          {isExtracting ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing OCR Layout...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5 text-cyan-200" />
              <span>Extract Measurements (OCR)</span>
            </>
          )}
        </button>
      )}
    </div>
  );
};
