import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { StatusBar } from './components/StatusBar';
import { ProductInputPanel } from './components/ProductInputPanel';
import { GarmentViewport } from './components/GarmentViewport';
import { ProductGarmentProperties } from './components/ProductGarmentProperties';

import { ModelMetadata, ShadingMode } from './types/garment';
import { MeasurementValues } from './types/measurements';
import { ProductDetails, SampleProductSummary } from './types/product';
import { api } from './services/api';

export const App: React.FC = () => {
  // Workflow Step: 1 = Source, 2 = Visual Analysis, 3 = Generation, 4 = Inspect & Export
  const [currentStep, setCurrentStep] = useState<number>(1);

  // E-Commerce Product State
  const [sampleProducts, setSampleProducts] = useState<SampleProductSummary[]>([]);
  const [currentProduct, setCurrentProduct] = useState<ProductDetails | null>(null);
  const [fit, setFit] = useState<string>('regular');

  // Direct Size Chart Parameters (Flipkart Standard: Chest, Shoulder, Length, Sleeve)
  const [unit, setUnit] = useState<'cm' | 'inch'>('cm');
  const [measurements, setMeasurements] = useState<MeasurementValues>({
    chest: 106,
    shoulder: 49,
    length: 71,
    sleeve: 21,
  });

  // Loading & Generation States
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Active 3D Model & Assets State
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [textureUrl, setTextureUrl] = useState<string | null>(null);
  const [modelMetadata, setModelMetadata] = useState<ModelMetadata | null>(null);
  const [shadingMode, setShadingMode] = useState<string>('textured');

  // Cache: `${productId}_${measSig}` -> { modelUrl, textureUrl, metadata }
  const [modelCache, setModelCache] = useState<Record<string, { modelUrl: string; textureUrl: string | null; metadata: ModelMetadata }>>({});

  // 1. Initial Load: Fetch sample products catalog
  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const res = await api.getSampleProducts();
        if (res.samples && res.samples.length > 0) {
          setSampleProducts(res.samples);
          // Automatically load the first sample product on start
          handleSelectSample(res.samples[0].id);
        }
      } catch (err) {
        console.error('Failed to load sample products:', err);
      }
    };
    fetchSamples();
  }, []);

  // 2. Select Sample Product
  const handleSelectSample = async (sampleId: string) => {
    setIsAnalyzing(true);
    setGenerationError(null);
    try {
      const prod = await api.analyzeProduct({ sample_id: sampleId });
      setCurrentProduct(prod);
      setCurrentStep(2);

      const measSig = `${measurements.chest}_${measurements.shoulder}_${measurements.length}_${measurements.sleeve}_${unit}`;
      const cacheKey = `${sampleId}_${measSig}`;
      if (modelCache[cacheKey]) {
        const cached = modelCache[cacheKey];
        setModelUrl(cached.modelUrl);
        setTextureUrl(cached.textureUrl);
        setModelMetadata(cached.metadata);
        setCurrentStep(4);
      } else {
        trigger3DGeneration(prod.product_id, measurements, unit);
      }
    } catch (err: any) {
      setGenerationError(err.message || 'Failed to analyze sample product');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 3. Analyze Flipkart URL
  const handleAnalyzeUrl = async (url: string) => {
    setIsAnalyzing(true);
    setGenerationError(null);
    try {
      const prod = await api.analyzeProduct({ url });
      setCurrentProduct(prod);
      setCurrentStep(2);
      trigger3DGeneration(prod.product_id, measurements, unit);
    } catch (err: any) {
      setGenerationError(err.message || 'Failed to analyze Flipkart product URL');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 4. Upload Custom Garment Photos
  const handleUploadCustomImages = async (frontFile: File, backFile?: File) => {
    setIsAnalyzing(true);
    setGenerationError(null);
    try {
      const formData = new FormData();
      formData.append('front_image', frontFile);
      if (backFile) {
        formData.append('back_image', backFile);
      }
      formData.append('title', frontFile.name.replace(/\.[^/.]+$/, ''));
      formData.append('brand', 'Custom Garment');

      const prod = await api.uploadProductImages(formData);
      setCurrentProduct(prod);
      setCurrentStep(2);
      trigger3DGeneration(prod.product_id, measurements, unit);
    } catch (err: any) {
      setGenerationError(err.message || 'Failed to analyze uploaded images');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 5. Trigger 3D Generation in Blender dynamically using exact size chart measurements
  const trigger3DGeneration = async (
    productId: string,
    customMeasurements?: MeasurementValues,
    customUnit?: string
  ) => {
    setIsGenerating(true);
    setGenerationProgress(15);
    setGenerationError(null);
    setCurrentStep(3);

    const activeMeas = customMeasurements || measurements;
    const activeUnit = customUnit || unit;

    try {
      const job = await api.generate3DFromProduct({
        product_id: productId,
        selected_size: 'custom',
        fit: fit,
        include_texture: true,
        measurements: activeMeas,
        unit: activeUnit,
      });

      if (job.status === 'failed') {
        throw new Error(job.error || 'Blender worker generation failed');
      }

      // Poll job progress
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getJobStatus(job.job_id);
          setGenerationProgress(status.progress);

          if (status.status === 'completed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setGenerationProgress(100);
            setCurrentStep(4);

            if (status.model_url) {
              setModelUrl(status.model_url);
            }
            if (status.texture_url) {
              setTextureUrl(status.texture_url);
            }
            if (status.metadata) {
              setModelMetadata(status.metadata);
            }

            // Save to cache with measurement signature
            if (status.model_url && status.metadata) {
              const measSig = `${activeMeas.chest}_${activeMeas.shoulder}_${activeMeas.length}_${activeMeas.sleeve}_${activeUnit}`;
              const cacheKey = `${productId}_${measSig}`;
              setModelCache((prev) => ({
                ...prev,
                [cacheKey]: {
                  modelUrl: status.model_url!,
                  textureUrl: status.texture_url || null,
                  metadata: status.metadata!,
                },
              }));
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setGenerationError(status.error || 'Garment generation failed');
          }
        } catch (pollErr: any) {
          clearInterval(pollInterval);
          setIsGenerating(false);
          setGenerationError(pollErr.message || 'Status polling error');
        }
      }, 700);
    } catch (err: any) {
      setIsGenerating(false);
      setGenerationError(err.message || 'Failed to start 3D generation');
    }
  };

  const handleManualGenerate = () => {
    if (currentProduct) {
      trigger3DGeneration(currentProduct.product_id, measurements, unit);
    }
  };

  const handleDownloadGLB = () => {
    if (!modelUrl) return;
    const cleanFilename = modelUrl.split('/').pop() || `garment_${measurements.chest}${unit}.glb`;
    const downloadUrl = `/api/models/${cleanFilename}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = cleanFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setCurrentStep(1);
    setCurrentProduct(null);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-studio-950 text-studio-100">
      {/* Top Studio Navigation */}
      <Header
        currentStep={currentStep}
        selectedSize={`${measurements.chest}${unit}`}
        isGenerating={isGenerating}
        hasModel={!!modelUrl}
        onOpenComparison={() => {}}
        onQuickExport={handleDownloadGLB}
        onReset={handleReset}
      />

      {/* Main Studio 3-Panel Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: Product URL / Samples / Custom Upload / Vision Analysis / Flipkart Size Chart */}
        <div className="w-84 md:w-96 h-full flex-shrink-0">
          <ProductInputPanel
            onAnalyzeUrl={handleAnalyzeUrl}
            onSelectSample={handleSelectSample}
            onUploadCustomImages={handleUploadCustomImages}
            sampleProducts={sampleProducts}
            currentProduct={currentProduct}
            measurements={measurements}
            unit={unit}
            onMeasurementsChange={setMeasurements}
            onUnitChange={setUnit}
            isAnalyzing={isAnalyzing}
            isGenerating={isGenerating}
            generationProgress={generationProgress}
            onGenerate3D={handleManualGenerate}
            hasModel={!!modelUrl}
            error={generationError}
            onClearError={() => setGenerationError(null)}
          />
        </div>

        {/* CENTER PANEL: Large Interactive 3D Viewport with Realistic Shading */}
        <div className="flex-1 relative h-full">
          <GarmentViewport
            modelUrl={modelUrl}
            textureUrl={textureUrl}
            metadata={modelMetadata}
            isGenerating={isGenerating}
            generationProgress={generationProgress}
            selectedSize={`${measurements.chest} ${unit}`}
            shadingMode={shadingMode as ShadingMode}
            onShadingModeChange={(mode) => setShadingMode(mode)}
          />
        </div>

        {/* RIGHT PANEL: 3D Garment Specs, UV Texture Map Preview & Downloads */}
        <div className="w-80 md:w-92 h-full flex-shrink-0">
          <ProductGarmentProperties
            metadata={modelMetadata}
            product={currentProduct}
            modelUrl={modelUrl}
            textureUrl={textureUrl}
            selectedSize={`${measurements.chest} ${unit} Chest`}
          />
        </div>
      </div>

      {/* Bottom Status Bar */}
      <StatusBar
        selectedSize={`${measurements.chest} ${unit}`}
        isGenerating={isGenerating}
        metadata={modelMetadata}
        shadingMode={shadingMode}
      />
    </div>
  );
};
