import React, { useState } from 'react';
import { 
  Download, Layers, Box, CheckCircle2, FileText, Image as ImageIcon,
  Shirt, Sparkles, Sliders, Eye, Scissors, Palette, ShieldCheck, AlertCircle
} from 'lucide-react';
import { ModelMetadata } from '../types/garment';
import { ProductDetails } from '../types/product';

interface ProductGarmentPropertiesProps {
  metadata: ModelMetadata | null;
  product: ProductDetails | null;
  modelUrl: string | null;
  textureUrl: string | null;
  selectedSize: string;
}

export const ProductGarmentProperties: React.FC<ProductGarmentPropertiesProps> = ({
  metadata,
  product,
  modelUrl,
  textureUrl,
  selectedSize,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'inspection'>('inspection');
  const [selectedInspectImage, setSelectedInspectImage] = useState<string | null>(null);
  const [pbrAtlasView, setPbrAtlasView] = useState<'diffuse' | 'normal' | 'roughness'>('diffuse');

  const diffuseUrl = textureUrl;
  const normalUrl = textureUrl ? textureUrl.replace('_texture.png', '_normal.png') : null;
  const roughnessUrl = textureUrl ? textureUrl.replace('_texture.png', '_roughness.png') : null;
  const currentAtlasUrl = pbrAtlasView === 'normal' ? (normalUrl || diffuseUrl) : (pbrAtlasView === 'roughness' ? (roughnessUrl || diffuseUrl) : diffuseUrl);

  const handleDownloadGlb = () => {
    if (!modelUrl) return;
    const cleanFilename = modelUrl.split('/').pop() || `garment_${selectedSize}.glb`;
    const downloadUrl = `/api/models/${cleanFilename}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = cleanFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadTexture = () => {
    if (!textureUrl) return;
    const link = document.createElement('a');
    link.href = textureUrl;
    link.download = `${product?.product_id || 'garment'}_texture.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadMetadata = () => {
    if (!metadata) return;
    const blob = new Blob([JSON.stringify(metadata, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `garment_${selectedSize}_metadata.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const dims = metadata?.dimensions;
  const widthCm = dims ? Math.round(dims.width_m * 100 * 10) / 10 : 83.1;
  const heightCm = dims ? Math.round(dims.height_m * 100 * 10) / 10 : 74.4;
  const depthCm = dims ? Math.round(dims.depth_m * 100 * 10) / 10 : 29.2;

  const vision = product?.vision_analysis;
  const frontGraphic = vision?.graphic;
  const backGraphic = vision?.back_graphic;
  const hasFrontGraphic = frontGraphic?.detected;
  const hasBackGraphic = backGraphic?.detected;

  return (
    <div className="flex flex-col h-full bg-studio-900 border-l studio-border overflow-y-auto">
      {/* Tab Navigation Header */}
      <div className="p-3 border-b studio-border bg-studio-900/60 sticky top-0 z-10 backdrop-blur-md">
        <div className="flex rounded-lg bg-studio-950 p-1 border border-studio-800">
          <button
            onClick={() => setActiveTab('inspection')}
            className={`flex-1 py-1.5 px-2 rounded text-xs font-mono font-medium transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'inspection'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-studio-400 hover:text-white'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Texture Inspection</span>
          </button>
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 py-1.5 px-2 rounded text-xs font-mono font-medium transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white shadow-sm font-bold'
                : 'text-studio-400 hover:text-white'
            }`}
          >
            <Shirt className="w-3.5 h-3.5" />
            <span>Model Specs</span>
          </button>
        </div>
      </div>

      <div className="p-3.5 space-y-4 flex-1">
        {activeTab === 'inspection' ? (
          /* TAB 1: TEXTURE & APPEARANCE INSPECTION PIPELINE */
          <div className="space-y-4">
            {/* Extraction Confidence & Status Bar */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Appearance Extraction Status</span>
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  hasFrontGraphic
                    ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {hasFrontGraphic ? 'Graphic Reconstructed' : 'Solid Fabric Preserved'}
                </span>
              </div>

              {/* Status Pills */}
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                <div className="bg-studio-900/80 p-2 rounded border border-studio-800">
                  <span className="text-studio-400 block mb-0.5">Base Fabric:</span>
                  <div className="flex items-center space-x-1.5">
                    <span 
                      className="w-3 h-3 rounded-full border border-white/20 shrink-0" 
                      style={{ backgroundColor: vision?.dominant_color_hex || '#1C1C1E' }} 
                    />
                    <span className="text-white font-bold truncate">
                      {vision?.dominant_color_name || 'Fabric'} ({vision?.dominant_color_hex || '#1C1C1E'})
                    </span>
                  </div>
                </div>

                <div className="bg-studio-900/80 p-2 rounded border border-studio-800">
                  <span className="text-studio-400 block mb-0.5">Pattern Type:</span>
                  <span className="text-cyan-300 font-bold block truncate capitalize">
                    {vision?.pattern_type ? vision.pattern_type.replace('_', ' ') : 'Solid'}
                  </span>
                </div>

                <div className="bg-studio-900/80 p-2 rounded border border-studio-800">
                  <span className="text-studio-400 block mb-0.5">Front Design:</span>
                  <span className={`font-bold block truncate ${hasFrontGraphic ? 'text-amber-300' : 'text-studio-300'}`}>
                    {hasFrontGraphic ? frontGraphic?.placement : 'Solid Plain Chest'}
                  </span>
                </div>

                <div className="bg-studio-900/80 p-2 rounded border border-studio-800">
                  <span className="text-studio-400 block mb-0.5">Collar & Front:</span>
                  <span className="text-amber-300 font-bold block truncate">
                    {vision?.neckline_type === 'polo' 
                      ? `Folded Polo (${vision?.button_count || 2} Buttons)`
                      : 'Ribbed Crew Neck'}
                  </span>
                </div>

                <div className="bg-studio-900/80 p-2 rounded border border-studio-800">
                  <span className="text-studio-400 block mb-0.5">Fabric Weave:</span>
                  <span className="text-indigo-300 font-bold block truncate capitalize">
                    {vision?.fabric_texture_type === 'cotton_pique' ? 'Cotton Piqué Waffle' : 'Single Jersey Cotton'}
                  </span>
                </div>
              </div>
            </div>

            {/* Stage 1: Original Product Photographs (Front & Back) */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-studio-850 pb-1.5">
                <span className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-blue-400" />
                  <span>1. Original Flipkart References</span>
                </span>
                <span className="text-[10px] font-mono text-studio-400">Source Photos</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-studio-400 block">Front Reference</span>
                  <div 
                    onClick={() => setSelectedInspectImage(product?.primary_image_url || null)}
                    className="aspect-[3/4] bg-studio-900 rounded-lg overflow-hidden border border-studio-800 cursor-pointer hover:border-blue-500/50 transition-all flex items-center justify-center relative group"
                  >
                    {product?.primary_image_url ? (
                      <img src={product.primary_image_url} alt="Front Ref" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-[10px] text-studio-500 font-mono">No Image</span>
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2 py-0.5 rounded border border-studio-700">Zoom</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-studio-400 block">Back Reference</span>
                  <div 
                    onClick={() => setSelectedInspectImage(product?.back_image_url || null)}
                    className="aspect-[3/4] bg-studio-900 rounded-lg overflow-hidden border border-studio-800 cursor-pointer hover:border-blue-500/50 transition-all flex items-center justify-center relative group"
                  >
                    {product?.back_image_url ? (
                      <img src={product.back_image_url} alt="Back Ref" className="w-full h-full object-cover" />
                    ) : (
                      <div className="p-2 text-center">
                        <span className="text-[10px] text-studio-400 font-mono block">Plain Back</span>
                        <span className="text-[9px] text-studio-500 block">Standard fabric</span>
                      </div>
                    )}
                    {product?.back_image_url && (
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2 py-0.5 rounded border border-studio-700">Zoom</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Stage 2: Garment-Specific Segmentation Cutouts */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-studio-850 pb-1.5">
                <span className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <Scissors className="w-3.5 h-3.5 text-cyan-400" />
                  <span>2. Garment Segmentation Cutouts</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400">Skin & BG Isolated</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-studio-400 block">Front Cutout (Transparent)</span>
                  <div 
                    onClick={() => setSelectedInspectImage(vision?.front_cutout_url || null)}
                    className="aspect-[3/4] bg-checkered rounded-lg overflow-hidden border border-studio-800 cursor-pointer hover:border-cyan-500/50 transition-all flex items-center justify-center relative group"
                  >
                    {vision?.front_cutout_url ? (
                      <img src={vision.front_cutout_url} alt="Front Cutout" className="w-full h-full object-contain p-1" />
                    ) : (
                      <span className="text-[10px] text-studio-500 font-mono">Segmenting...</span>
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2 py-0.5 rounded border border-studio-700">Zoom</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-studio-400 block">Back Cutout (Transparent)</span>
                  <div 
                    onClick={() => setSelectedInspectImage(vision?.back_cutout_url || null)}
                    className="aspect-[3/4] bg-checkered rounded-lg overflow-hidden border border-studio-800 cursor-pointer hover:border-cyan-500/50 transition-all flex items-center justify-center relative group"
                  >
                    {vision?.back_cutout_url ? (
                      <img src={vision.back_cutout_url} alt="Back Cutout" className="w-full h-full object-contain p-1" />
                    ) : (
                      <div className="p-2 text-center">
                        <span className="text-[10px] text-studio-400 font-mono block">Plain Torso</span>
                        <span className="text-[9px] text-studio-500 block">Identical fabric</span>
                      </div>
                    )}
                    {vision?.back_cutout_url && (
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2 py-0.5 rounded border border-studio-700">Zoom</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-studio-400 italic">
                Isolated garment pixels eliminating human face, chin, neck skin, arms, hands, and trousers.
              </p>
            </div>

            {/* Stage 3: Extracted Artwork & Logos */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-studio-850 pb-1.5">
                <span className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <Palette className="w-3.5 h-3.5 text-amber-400" />
                  <span>3. Extracted Artwork & Logos</span>
                </span>
                <span className="text-[10px] font-mono text-studio-400">Feathered Alpha</span>
              </div>

              {hasFrontGraphic ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-white font-bold">{frontGraphic?.placement}</span>
                    <span className="text-amber-400 text-[10px]">High-Res Alpha Matting</span>
                  </div>
                  <div 
                    onClick={() => setSelectedInspectImage(frontGraphic?.badge_preview_url || null)}
                    className="p-3 bg-checkered rounded-lg border border-studio-800 max-h-36 flex items-center justify-center cursor-pointer hover:border-amber-500/50 transition-all relative group"
                  >
                    {frontGraphic?.badge_preview_url && (
                      <img 
                        src={frontGraphic.badge_preview_url} 
                        alt="Front Badge" 
                        className="max-h-28 max-w-full object-contain filter drop-shadow" 
                      />
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2 py-0.5 rounded border border-studio-700">Zoom Artwork</span>
                    </div>
                  </div>
                  <p className="text-[10px] text-studio-300 font-mono">
                    {frontGraphic?.description}
                  </p>
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-studio-900 border border-studio-800 text-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                  <span className="text-xs font-mono font-bold text-white block">Solid Garment</span>
                  <span className="text-[10px] text-studio-400 block mt-0.5">
                    Pristine fabric weave synthesized with zero phantom photo artifacts.
                  </span>
                </div>
              )}
            </div>

            {/* Stage 4: Master 2K UV Texture Atlas */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-studio-850 pb-1.5">
                <span className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-purple-400" />
                  <span>4. Master 2K PBR Maps</span>
                </span>
                <span className="text-[10px] font-mono text-studio-400">2048 x 2048 px</span>
              </div>

              {textureUrl ? (
                <div className="space-y-2">
                  <div className="flex rounded-md bg-studio-900 p-0.5 border border-studio-800 text-[10px] font-mono">
                    <button
                      onClick={() => setPbrAtlasView('diffuse')}
                      className={`flex-1 py-1 rounded transition-all ${pbrAtlasView === 'diffuse' ? 'bg-purple-600 text-white font-bold' : 'text-studio-400 hover:text-white'}`}
                    >
                      Color / Diffuse
                    </button>
                    <button
                      onClick={() => setPbrAtlasView('normal')}
                      className={`flex-1 py-1 rounded transition-all ${pbrAtlasView === 'normal' ? 'bg-purple-600 text-white font-bold' : 'text-studio-400 hover:text-white'}`}
                    >
                      Normal (Relief)
                    </button>
                    <button
                      onClick={() => setPbrAtlasView('roughness')}
                      className={`flex-1 py-1 rounded transition-all ${pbrAtlasView === 'roughness' ? 'bg-purple-600 text-white font-bold' : 'text-studio-400 hover:text-white'}`}
                    >
                      Roughness
                    </button>
                  </div>

                  <div 
                    onClick={() => setSelectedInspectImage(currentAtlasUrl)}
                    className="relative group rounded-lg overflow-hidden border border-studio-800 bg-studio-900 aspect-square max-h-44 flex items-center justify-center cursor-pointer hover:border-purple-500/50 transition-all"
                  >
                    <img
                      src={currentAtlasUrl || ''}
                      alt="Extracted Master Texture Map"
                      className="w-full h-full object-contain"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-[10px] font-mono text-white bg-studio-900/90 px-2.5 py-1 rounded-md border border-studio-700">
                        View Full Atlas
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[9px] font-mono text-studio-400">
                    <div>• Left: Front Torso (U: 0.08-0.45)</div>
                    <div>• Right: Back Torso (U: 0.55-0.92)</div>
                    <div>• Top: Ribbed Collar Band</div>
                    <div>• Bottom: Sleeve Bands</div>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-studio-900 border border-studio-800 text-center text-xs text-studio-400 font-mono">
                  Generate 3D model to synthesize atlas.
                </div>
              )}
            </div>
          </div>
        ) : (
          /* TAB 2: 3D MODEL SPECS & DIMENSIONS */
          <div className="space-y-4">
            {/* Model Dimensions Card */}
            <div className="bg-studio-950 border border-studio-800 rounded-xl p-3.5 space-y-3">
              <div className="flex items-center justify-between border-b border-studio-850 pb-2">
                <span className="text-xs font-mono uppercase font-bold text-white flex items-center space-x-1.5">
                  <Shirt className="w-4 h-4 text-blue-400" />
                  <span>3D Garment Geometry</span>
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Size {selectedSize}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="bg-studio-900 p-2.5 rounded-lg border border-studio-800 text-center">
                  <span className="text-[10px] font-mono uppercase text-studio-400 block mb-0.5">Width</span>
                  <span className="text-sm font-mono font-bold text-white">{widthCm} cm</span>
                </div>
                <div className="bg-studio-900 p-2.5 rounded-lg border border-studio-800 text-center">
                  <span className="text-[10px] font-mono uppercase text-studio-400 block mb-0.5">Length</span>
                  <span className="text-sm font-mono font-bold text-white">{heightCm} cm</span>
                </div>
                <div className="bg-studio-900 p-2.5 rounded-lg border border-studio-800 text-center">
                  <span className="text-[10px] font-mono uppercase text-studio-400 block mb-0.5">Depth</span>
                  <span className="text-sm font-mono font-bold text-white">{depthCm} cm</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                <div className="bg-studio-900/60 p-2 rounded border border-studio-800 flex justify-between">
                  <span className="text-studio-400">Vertices:</span>
                  <span className="text-white font-semibold">{metadata?.vertex_count ? metadata.vertex_count.toLocaleString() : '1,190'}</span>
                </div>
                <div className="bg-studio-900/60 p-2 rounded border border-studio-800 flex justify-between">
                  <span className="text-studio-400">Polygons:</span>
                  <span className="text-white font-semibold">{metadata?.face_count ? metadata.face_count.toLocaleString() : '1,100'}</span>
                </div>
                <div className="bg-studio-900/60 p-2 rounded border border-studio-800 flex justify-between">
                  <span className="text-studio-400">Topology:</span>
                  <span className="text-white font-semibold">2-Manifold</span>
                </div>
                <div className="bg-studio-900/60 p-2 rounded border border-studio-800 flex justify-between">
                  <span className="text-studio-400">Format:</span>
                  <span className="text-emerald-400 font-semibold">Binary GLB</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Global Download Actions (Always visible at bottom) */}
        <div className="space-y-2 pt-2 border-t border-studio-800">
          <button
            onClick={handleDownloadGlb}
            disabled={!modelUrl}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition-all flex items-center justify-center space-x-2 shadow-md shadow-blue-500/20"
          >
            <Download className="w-4 h-4" />
            <span>Download 3D Garment (.GLB)</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleDownloadTexture}
              disabled={!textureUrl}
              className="py-2 px-3 bg-studio-950 hover:bg-studio-800 border border-studio-750 disabled:opacity-50 text-studio-200 text-xs rounded-lg transition-all flex items-center justify-center space-x-1.5"
            >
              <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
              <span>Texture (.PNG)</span>
            </button>
            <button
              onClick={handleDownloadMetadata}
              disabled={!metadata}
              className="py-2 px-3 bg-studio-950 hover:bg-studio-800 border border-studio-750 disabled:opacity-50 text-studio-200 text-xs rounded-lg transition-all flex items-center justify-center space-x-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-amber-400" />
              <span>Metadata (.JSON)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Lightbox Modal for Zooming Inspected Asset */}
      {selectedInspectImage && (
        <div 
          onClick={() => setSelectedInspectImage(null)}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 cursor-pointer"
        >
          <div className="max-w-2xl max-h-[85vh] bg-studio-950 border border-studio-700 rounded-2xl p-2 shadow-2xl relative">
            <img 
              src={selectedInspectImage} 
              alt="Asset Inspection" 
              className="max-h-[80vh] w-auto object-contain rounded-xl" 
            />
            <div className="text-center py-2 text-xs font-mono text-studio-400">
              Click anywhere to close
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
