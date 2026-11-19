import React, { useState } from 'react';
import { 
  Globe, Sparkles, Upload, Loader2, Image as ImageIcon, CheckCircle2,
  Tag, Palette, Shirt, ExternalLink, RefreshCw, Ruler, AlertCircle, X
} from 'lucide-react';
import { ProductDetails, SampleProductSummary } from '../types/product';
import { MeasurementValues, ChestMeasurementType } from '../types/measurements';
import { GarmentType } from '../types/garment';

interface ProductInputPanelProps {
  garmentType: GarmentType;
  onGarmentTypeChange: (type: GarmentType) => void;
  onAnalyzeUrl: (url: string) => Promise<void>;
  onSelectSample: (sampleId: string) => Promise<void>;
  onUploadCustomImages: (frontFile: File, backFile?: File) => Promise<void>;
  sampleProducts: SampleProductSummary[];
  currentProduct: ProductDetails | null;
  measurements: MeasurementValues;
  unit: 'cm' | 'inch';
  onMeasurementsChange: (meas: MeasurementValues) => void;
  onUnitChange: (unit: 'cm' | 'inch') => void;
  isAnalyzing: boolean;
  isGenerating: boolean;
  generationProgress: number;
  onGenerate3D: () => void;
  hasModel: boolean;
  error?: string | null;
  onClearError?: () => void;
}

export const ProductInputPanel: React.FC<ProductInputPanelProps> = ({
  garmentType,
  onGarmentTypeChange,
  onAnalyzeUrl,
  onSelectSample,
  onUploadCustomImages,
  sampleProducts,
  currentProduct,
  measurements,
  unit,
  onMeasurementsChange,
  onUnitChange,
  isAnalyzing,
  isGenerating,
  generationProgress,
  onGenerate3D,
  hasModel,
  error,
  onClearError
}) => {
  const [activeTab, setActiveTab] = useState<'url' | 'sample' | 'upload'>('url');
  const [urlInput, setUrlInput] = useState('');
  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [backFile, setBackFile] = useState<File | null>(null);

  const flipkartPresets = [
    { tag: '38" (S)', chestCm: 96, chestIn: 38, shoulderCm: 44, shoulderIn: 17.3, lengthCm: 68, lengthIn: 26.8, sleeveCm: 20, sleeveIn: 7.9 },
    { tag: '40" (M)', chestCm: 101, chestIn: 40, shoulderCm: 46, shoulderIn: 18.1, lengthCm: 70, lengthIn: 27.6, sleeveCm: 21, sleeveIn: 8.3 },
    { tag: '42" (L)', chestCm: 106, chestIn: 42, shoulderCm: 48, shoulderIn: 18.9, lengthCm: 72, lengthIn: 28.3, sleeveCm: 22, sleeveIn: 8.7 },
    { tag: '44" (XL)', chestCm: 112, chestIn: 44, shoulderCm: 50, shoulderIn: 19.7, lengthCm: 74, lengthIn: 29.1, sleeveCm: 23, sleeveIn: 9.1 },
    { tag: '46" (XXL)', chestCm: 118, chestIn: 46.5, shoulderCm: 52, shoulderIn: 20.5, lengthCm: 76, lengthIn: 29.9, sleeveCm: 24, sleeveIn: 9.4 },
  ];

  const handleFieldChange = (field: keyof MeasurementValues, value: number) => {
    onMeasurementsChange({
      ...measurements,
      [field]: Math.max(0, value)
    });
  };

  const handleUnitToggle = (newUnit: 'cm' | 'inch') => {
    if (newUnit === unit) return;
    const factor = newUnit === 'inch' ? (1 / 2.54) : 2.54;
    onUnitChange(newUnit);
    onMeasurementsChange({
      ...measurements,
      chest: Math.max(0, Math.round(measurements.chest * factor * 10) / 10),
      shoulder: Math.max(0, Math.round(measurements.shoulder * factor * 10) / 10),
      length: Math.max(0, Math.round(measurements.length * factor * 10) / 10),
      sleeve: measurements.sleeve !== undefined && measurements.sleeve !== null 
        ? Math.max(0, Math.round(measurements.sleeve * factor * 10) / 10)
        : null,
    });
  };

  const applyPreset = (p: typeof flipkartPresets[0]) => {
    onMeasurementsChange({
      ...measurements,
      chest: unit === 'inch' ? p.chestIn : p.chestCm,
      shoulder: unit === 'inch' ? p.shoulderIn : p.shoulderCm,
      length: unit === 'inch' ? p.lengthIn : p.lengthCm,
      sleeve: unit === 'inch' ? p.sleeveIn : p.sleeveCm,
    });
  };

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (urlInput.trim()) {
      onAnalyzeUrl(urlInput.trim());
    }
  };

  const handleCustomUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (frontFile) {
      onUploadCustomImages(frontFile, backFile || undefined);
    }
  };

  return (
    <div className="flex flex-col h-full bg-studio-900 border-r studio-border overflow-y-auto">
      {/* Panel Header */}
      <div className="p-4 border-b studio-border bg-studio-900/50">
        <h2 className="text-xs font-mono uppercase tracking-wider text-studio-400 font-bold mb-1">
          1. E-Commerce Product Source
        </h2>
        <p className="text-xs text-studio-300">
          Transform a Flipkart apparel listing into a textured 3D garment.
        </p>

        {/* Source Tabs */}
        <div className="flex rounded-lg bg-studio-950 p-1 mt-3 border border-studio-800">
          <button
            onClick={() => setActiveTab('url')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'url' ? 'bg-blue-600 text-white shadow-sm' : 'text-studio-400 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Product URL</span>
          </button>
          <button
            onClick={() => setActiveTab('sample')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'sample' ? 'bg-blue-600 text-white shadow-sm' : 'text-studio-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Try Samples</span>
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'upload' ? 'bg-blue-600 text-white shadow-sm' : 'text-studio-400 hover:text-white'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Custom Photo</span>
          </button>
        </div>
      </div>

      {/* Input Section according to Active Tab */}
      <div className="p-4 border-b studio-border">
        {activeTab === 'url' && (
          <form onSubmit={handleUrlSubmit} className="space-y-3">
            <div>
              <label className="block text-[11px] font-mono text-studio-400 mb-1.5 uppercase">
                Flipkart Product URL
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="https://www.flipkart.com/.../p/..."
                  value={urlInput}
                  onChange={(e) => {
                    setUrlInput(e.target.value);
                    if (error && onClearError) onClearError();
                  }}
                  className="w-full bg-studio-950 border border-studio-750 focus:border-blue-500 rounded-lg px-3 py-2 text-xs text-white placeholder-studio-500 outline-none transition-colors"
                />
              </div>
            </div>

            {error && (
              <div className="p-2.5 bg-red-950/70 border border-red-800/80 rounded-lg text-xs text-red-200 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <span className="flex-1 text-[11px] leading-tight">{error}</span>
                {onClearError && (
                  <button type="button" onClick={onClearError} className="text-red-400 hover:text-white">
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={isAnalyzing || !urlInput.trim()}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition-all flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/10"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting & Analyzing Product...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Analyze Product & Extract Design</span>
                </>
              )}
            </button>
          </form>
        )}

        {activeTab === 'sample' && (
          <div className="space-y-2">
            <label className="block text-[11px] font-mono text-studio-400 mb-2 uppercase">
              Curated Showcase Garments
            </label>
            <div className="grid grid-cols-1 gap-2">
              {sampleProducts.map((sample) => (
                <button
                  key={sample.id}
                  onClick={() => onSelectSample(sample.id)}
                  disabled={isAnalyzing}
                  className={`flex items-center space-x-3 p-2 rounded-lg border text-left transition-all ${
                    currentProduct?.product_id === sample.id
                      ? 'border-blue-500 bg-blue-500/10 ring-1 ring-blue-500'
                      : 'border-studio-800 bg-studio-950/60 hover:border-studio-700 hover:bg-studio-950'
                  }`}
                >
                  <img
                    src={sample.thumbnail}
                    alt={sample.title}
                    className="w-12 h-14 object-cover rounded bg-studio-900 border border-studio-800 flex-shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white truncate">{sample.brand}</span>
                      <span className="text-[11px] font-mono font-bold text-emerald-400">{sample.price}</span>
                    </div>
                    <p className="text-[11px] text-studio-300 truncate">{sample.title}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span
                        className="w-3 h-3 rounded-full border border-white/20 inline-block"
                        style={{ backgroundColor: sample.base_color_hex }}
                      />
                      <span className="text-[10px] text-studio-400 font-mono">{sample.color_name}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'upload' && (
          <form onSubmit={handleCustomUpload} className="space-y-3">
            <div>
              <label className="block text-[11px] font-mono text-studio-400 mb-1.5 uppercase">
                Front Garment Photo (Required)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFrontFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-studio-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-studio-800 file:text-white hover:file:bg-studio-700 cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-studio-400 mb-1.5 uppercase">
                Back Garment Photo (Optional)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setBackFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-studio-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-studio-800 file:text-white hover:file:bg-studio-700 cursor-pointer"
              />
            </div>
            <button
              type="submit"
              disabled={isAnalyzing || !frontFile}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition-all flex items-center justify-center space-x-2"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing Upload...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Analyze Garment</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>

      {/* Extracted Product Overview & Vision Card */}
      {currentProduct && (
        <div className="p-4 space-y-4 flex-1">
          {/* Product Overview Card */}
          <div className="bg-studio-950 border border-studio-800 rounded-xl p-3.5 space-y-3 shadow-md">
            <div className="flex items-start space-x-3">
              <img
                src={currentProduct.primary_image_url}
                alt={currentProduct.title}
                className="w-16 h-20 object-cover rounded-lg bg-studio-900 border border-studio-800 flex-shrink-0"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center space-x-2 mb-0.5">
                  <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {currentProduct.brand}
                  </span>
                  {currentProduct.price && (
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      {currentProduct.price}
                    </span>
                  )}
                </div>
                <h3 className="text-xs font-medium text-white line-clamp-2 leading-tight">
                  {currentProduct.title}
                </h3>
                <p className="text-[11px] text-studio-400 mt-1 line-clamp-1">
                  {currentProduct.description}
                </p>
              </div>
            </div>

            {/* Gallery Images Strip */}
            {currentProduct.gallery_images && currentProduct.gallery_images.length > 0 && (
              <div>
                <span className="text-[10px] font-mono uppercase text-studio-500 block mb-1.5">
                  Product Gallery ({currentProduct.gallery_images.length} views)
                </span>
                <div className="flex space-x-2 overflow-x-auto pb-1">
                  {currentProduct.gallery_images.map((imgUrl, i) => (
                    <img
                      key={i}
                      src={imgUrl}
                      alt={`Gallery view ${i}`}
                      className="w-10 h-12 object-cover rounded border border-studio-800 bg-studio-900 flex-shrink-0"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Vision Analysis Results */}
          <div className="bg-studio-950 border border-studio-800 rounded-xl p-3.5 space-y-3">
            <div className="flex items-center justify-between border-b border-studio-850 pb-2">
              <div className="flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h4 className="text-xs font-mono uppercase font-bold text-studio-300">
                  AI Garment Vision Analysis
                </h4>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Verified</span>
              </span>
            </div>

            {/* Colors */}
            <div>
              <span className="text-[10px] font-mono uppercase text-studio-400 block mb-1">
                Dominant Garment Color
              </span>
              <div className="flex items-center space-x-2.5 bg-studio-900 p-2 rounded-lg border border-studio-800">
                <div
                  className="w-6 h-6 rounded-md border border-white/30 shadow-inner flex-shrink-0"
                  style={{ backgroundColor: currentProduct.vision_analysis.dominant_color_hex }}
                />
                <div className="min-w-0">
                  <span className="text-xs font-semibold text-white block">
                    {currentProduct.vision_analysis.dominant_color_name}
                  </span>
                  <span className="text-[10px] font-mono text-studio-400">
                    {currentProduct.vision_analysis.dominant_color_hex}
                  </span>
                </div>
                {currentProduct.vision_analysis.secondary_colors.length > 0 && (
                  <div className="ml-auto flex items-center space-x-1">
                    {currentProduct.vision_analysis.secondary_colors.map((c, idx) => (
                      <div
                        key={idx}
                        className="w-4 h-4 rounded-full border border-white/20"
                        style={{ backgroundColor: c }}
                        title={`Accent: ${c}`}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Extracted Graphic Prints & Artwork (Front / Back / Details) */}
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase text-studio-400 block font-semibold">
                Extracted Prints & Graphics
              </span>

              {/* Front Print */}
              <div className="bg-studio-900 p-2.5 rounded-lg border border-studio-800 flex items-center space-x-3">
                {currentProduct.vision_analysis.graphic.detected && currentProduct.vision_analysis.graphic.badge_preview_url ? (
                  <img
                    src={currentProduct.vision_analysis.graphic.badge_preview_url}
                    alt="Front Print"
                    className="w-12 h-12 object-contain rounded bg-studio-950 p-1 border border-studio-800 flex-shrink-0"
                  />
                ) : (
                  <div className="w-12 h-12 rounded bg-studio-950 flex items-center justify-center border border-studio-800 text-studio-500 flex-shrink-0">
                    <Shirt className="w-5 h-5" />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-1.5 mb-0.5">
                    <span className="text-[10px] font-mono font-bold text-studio-300">FRONT:</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                      currentProduct.vision_analysis.graphic.detected
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-studio-800 text-studio-400'
                    }`}>
                      {currentProduct.vision_analysis.graphic.placement || 'Solid'}
                    </span>
                  </div>
                  <p className="text-[11px] text-studio-300 line-clamp-1">
                    {currentProduct.vision_analysis.graphic.description || 'Solid chest panel'}
                  </p>
                </div>
              </div>

              {/* Back Print */}
              <div className="bg-studio-900 p-2.5 rounded-lg border border-studio-800 flex items-center space-x-3">
                {currentProduct.vision_analysis.back_graphic?.detected && currentProduct.vision_analysis.back_graphic?.badge_preview_url ? (
                  <img
                    src={currentProduct.vision_analysis.back_graphic.badge_preview_url}
                    alt="Back Print"
                    className="w-12 h-12 object-contain rounded bg-studio-950 p-1 border border-studio-800 flex-shrink-0"
                  />
                ) : (
                  <div className="w-12 h-12 rounded bg-studio-950 flex items-center justify-center border border-studio-800 text-emerald-400 flex-shrink-0">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-1.5 mb-0.5">
                    <span className="text-[10px] font-mono font-bold text-studio-300">BACK:</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                      currentProduct.vision_analysis.back_graphic?.detected
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                    {currentProduct.vision_analysis.back_graphic?.detected ? currentProduct.vision_analysis.back_graphic.placement : 'Plain Clean Back'}
                    </span>
                  </div>
                  <p className="text-[11px] text-studio-300 line-clamp-1">
                    {currentProduct.vision_analysis.back_graphic?.description || 'Authentic seamless matching back fabric'}
                  </p>
                </div>
              </div>
            </div>

            {/* Structural Geometry Badges */}
            <div className="grid grid-cols-3 gap-1.5 pt-1">
              <div className="bg-studio-900 p-2 rounded-lg border border-studio-800 text-center">
                <span className="text-[9px] font-mono uppercase text-studio-400 block">Silhouette</span>
                <span className="text-xs font-semibold text-white capitalize">
                  {currentProduct.vision_analysis.silhouette} Fit
                </span>
              </div>
              <div className="bg-studio-900 p-2 rounded-lg border border-studio-800 text-center">
                <span className="text-[9px] font-mono uppercase text-studio-400 block">Neckline</span>
                <span className="text-xs font-semibold text-white capitalize">
                  {currentProduct.vision_analysis.neckline_type === 'round' ? 'Crew Neck' : currentProduct.vision_analysis.neckline_type}
                </span>
              </div>
              <div className="bg-studio-900 p-2 rounded-lg border border-studio-800 text-center">
                <span className="text-[9px] font-mono uppercase text-studio-400 block">Sleeves</span>
                <span className="text-xs font-semibold text-white capitalize">
                  {currentProduct.vision_analysis.sleeve_type} Sleeve
                </span>
              </div>
            </div>
          </div>

          {/* Garment Type Selector: Plain Crew-Neck vs Polo T-Shirt */}
          <div className="space-y-2 pt-3 border-t border-studio-800">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                <Shirt className="w-3.5 h-3.5 text-indigo-400" />
                <span>Garment Type</span>
              </h4>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold border ${
                garmentType === 'polo' 
                  ? 'bg-indigo-950/80 border-indigo-700/60 text-indigo-300' 
                  : 'bg-blue-950/80 border-blue-700/60 text-blue-300'
              }`}>
                {garmentType === 'polo' ? 'Polo Neck' : 'Plain Crew Neck'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {/* Option 1: Plain Crew-Neck T-Shirt */}
              <button
                type="button"
                onClick={() => onGarmentTypeChange('basic_crew')}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  garmentType === 'basic_crew'
                    ? 'bg-blue-950/60 border-blue-500 shadow-md shadow-blue-500/20 ring-1 ring-blue-500'
                    : 'bg-studio-950 border-studio-800 hover:border-studio-700 opacity-75'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">Plain T-Shirt</span>
                  {garmentType === 'basic_crew' && <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />}
                </div>
                <p className="text-[10px] text-studio-400 leading-tight">
                  Hollow round crew-neck, 1x1 ribbed collar, single jersey cotton.
                </p>
              </button>

              {/* Option 2: Polo T-Shirt */}
              <button
                type="button"
                onClick={() => onGarmentTypeChange('polo')}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  garmentType === 'polo'
                    ? 'bg-indigo-950/60 border-indigo-500 shadow-md shadow-indigo-500/20 ring-1 ring-indigo-500'
                    : 'bg-studio-950 border-studio-800 hover:border-studio-700 opacity-75'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">Polo T-Shirt</span>
                  {garmentType === 'polo' && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />}
                </div>
                <p className="text-[10px] text-studio-400 leading-tight">
                  Folded 3D collar, stand, front button placket, cotton piqué knit.
                </p>
              </button>
            </div>
          </div>

          {/* Size Chart Parameters (Flipkart / E-Commerce Standard) */}
          <div className="space-y-3 pt-3 border-t border-studio-800">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <Ruler className="w-3.5 h-3.5 text-blue-400" />
                  <span>Size Chart Parameters</span>
                </h4>
                <p className="text-[10px] text-studio-400 mt-0.5">
                  Direct physical garment measurements
                </p>
              </div>

              {/* Unit Toggle */}
              <div className="flex items-center bg-studio-950 border border-studio-800 rounded p-0.5 text-[11px] font-mono">
                <button
                  type="button"
                  onClick={() => handleUnitToggle('cm')}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    unit === 'cm' ? 'bg-blue-600 text-white font-bold' : 'text-studio-400 hover:text-white'
                  }`}
                >
                  CM
                </button>
                <button
                  type="button"
                  onClick={() => handleUnitToggle('inch')}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    unit === 'inch' ? 'bg-blue-600 text-white font-bold' : 'text-studio-400 hover:text-white'
                  }`}
                >
                  INCH
                </button>
              </div>
            </div>

            {/* Chest Definition Toggle: Full Circumference vs Flat Width */}
            <div className="flex items-center justify-between bg-studio-950 border border-studio-800 rounded-lg px-2.5 py-1.5 text-[10px]">
              <span className="text-studio-400 font-mono font-medium">Chest Definition:</span>
              <div className="flex space-x-1">
                <button
                  type="button"
                  onClick={() => onMeasurementsChange({ ...measurements, chest_measurement_type: 'circumference' })}
                  className={`px-2 py-0.5 rounded transition-colors font-mono ${
                    (measurements.chest_measurement_type || 'circumference') === 'circumference'
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-studio-400 hover:text-white'
                  }`}
                  title="Full 360-degree circumference around torso"
                >
                  Full Loop (360°)
                </button>
                <button
                  type="button"
                  onClick={() => onMeasurementsChange({ ...measurements, chest_measurement_type: 'flat_width' })}
                  className={`px-2 py-0.5 rounded transition-colors font-mono ${
                    measurements.chest_measurement_type === 'flat_width'
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-studio-400 hover:text-white'
                  }`}
                  title="Flat pit-to-pit width straight across front of garment"
                >
                  Flat Width (Pit-to-Pit)
                </button>
              </div>
            </div>

            {/* Core 3 Parameters: CHEST, SHOULDER, LENGTH */}
            <div className="grid grid-cols-3 gap-2">
              {/* 1. CHEST */}
              <div className="bg-studio-950 p-2.5 rounded-lg border border-studio-800 focus-within:border-blue-500 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] font-mono uppercase font-bold text-blue-400">
                    Chest
                  </label>
                  <span className="text-[9px] font-mono text-studio-500">{unit}</span>
                </div>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={measurements.chest || ''}
                  onChange={(e) => handleFieldChange('chest', Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full bg-studio-900 border border-studio-750 rounded px-1.5 py-1 text-sm font-mono font-bold text-white text-center focus:outline-none focus:border-blue-400"
                  placeholder="106"
                />
                <span className="text-[9px] text-studio-400 block text-center mt-1 truncate">
                  Circumference
                </span>
              </div>

              {/* 2. SHOULDER */}
              <div className="bg-studio-950 p-2.5 rounded-lg border border-studio-800 focus-within:border-cyan-500 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] font-mono uppercase font-bold text-cyan-400">
                    Shoulder
                  </label>
                  <span className="text-[9px] font-mono text-studio-500">{unit}</span>
                </div>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={measurements.shoulder || ''}
                  onChange={(e) => handleFieldChange('shoulder', Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full bg-studio-900 border border-studio-750 rounded px-1.5 py-1 text-sm font-mono font-bold text-white text-center focus:outline-none focus:border-cyan-400"
                  placeholder="49"
                />
                <span className="text-[9px] text-studio-400 block text-center mt-1 truncate">
                  Width Span
                </span>
              </div>

              {/* 3. LENGTH */}
              <div className="bg-studio-950 p-2.5 rounded-lg border border-studio-800 focus-within:border-indigo-500 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] font-mono uppercase font-bold text-indigo-400">
                    Length
                  </label>
                  <span className="text-[9px] font-mono text-studio-500">{unit}</span>
                </div>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={measurements.length || ''}
                  onChange={(e) => handleFieldChange('length', Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full bg-studio-900 border border-studio-750 rounded px-1.5 py-1 text-sm font-mono font-bold text-white text-center focus:outline-none focus:border-indigo-400"
                  placeholder="71"
                />
                <span className="text-[9px] text-studio-400 block text-center mt-1 truncate">
                  HPS to Hem
                </span>
              </div>
            </div>

            {/* Sleeve Length & Proportions */}
            <div className="flex items-center space-x-2 bg-studio-950 p-2 rounded-lg border border-studio-800">
              <span className="text-[10px] font-mono uppercase text-studio-400 whitespace-nowrap">
                Sleeve Length:
              </span>
              <input
                type="number"
                min="0"
                step="0.5"
                value={measurements.sleeve || ''}
                onChange={(e) => handleFieldChange('sleeve', Math.max(0, parseFloat(e.target.value) || 0))}
                className="w-20 bg-studio-900 border border-studio-750 rounded px-2 py-0.5 text-xs font-mono font-semibold text-white text-center focus:outline-none focus:border-blue-400"
                placeholder="21"
              />
              <span className="text-[10px] font-mono text-studio-500">{unit}</span>
              <span className="text-[10px] text-studio-500 ml-auto italic">Short sleeve</span>
            </div>

            {/* Quick Fill Size Presets (Flipkart Size Chart Standards) */}
            <div>
              <span className="text-[10px] font-mono uppercase text-studio-400 block mb-1.5">
                Quick Fill Presets (Flipkart Standard)
              </span>
              <div className="grid grid-cols-5 gap-1.5">
                {flipkartPresets.map((p) => {
                  const targetChest = unit === 'inch' ? p.chestIn : p.chestCm;
                  const isActive = Math.abs(measurements.chest - targetChest) < 1.0;
                  return (
                    <button
                      key={p.tag}
                      type="button"
                      onClick={() => applyPreset(p)}
                      className={`py-1.5 px-1 text-center rounded border transition-all ${
                        isActive
                          ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-500/20 font-bold'
                          : 'bg-studio-950 text-studio-300 border-studio-800 hover:border-studio-700 hover:text-white'
                      }`}
                    >
                      <span className="text-[11px] font-mono block leading-none">{p.tag}</span>
                      <span className="text-[9px] text-studio-400 block mt-0.5 leading-none">
                        {unit === 'inch' ? `${p.chestIn}"` : `${p.chestCm}cm`}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Primary Action Button */}
          <div className="pt-2">
            <button
              onClick={onGenerate3D}
              disabled={isGenerating}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating 3D Model ({generationProgress}%)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>
                    {hasModel
                      ? (garmentType === 'polo' ? '⚡ Regenerate 3D Polo T-Shirt' : '⚡ Regenerate 3D Plain Crew T-Shirt')
                      : (garmentType === 'polo' ? '✨ Generate 3D Polo T-Shirt' : '✨ Generate 3D Plain Crew T-Shirt')}
                  </span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
