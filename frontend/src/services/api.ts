import { SizeChartData, UploadResponse, MeasurementValues } from '../types/measurements';
import { GarmentConfiguration, GenerationJobResponse, ModelMetadata } from '../types/garment';
import { ProductDetails, SampleProductSummary } from '../types/product';

const BASE_URL = '/api';

export const api = {
  // --- AI E-Commerce Product to 3D Endpoints ---

  // 1. Get curated sample products
  async getSampleProducts(): Promise<{ samples: SampleProductSummary[] }> {
    const res = await fetch(`${BASE_URL}/products/samples`);
    if (!res.ok) {
      throw new Error('Failed to load sample products');
    }
    return res.json();
  },

  // 2. Get sample product details
  async getSampleDetails(sampleId: string): Promise<ProductDetails> {
    const res = await fetch(`${BASE_URL}/products/samples/${sampleId}`);
    if (!res.ok) {
      throw new Error(`Failed to load sample product ${sampleId}`);
    }
    return res.json();
  },

  // 3. Analyze Flipkart URL or sample
  async analyzeProduct(params: { url?: string; sample_id?: string }): Promise<ProductDetails> {
    const res = await fetch(`${BASE_URL}/products/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Product analysis failed' }));
      throw new Error(err.detail || 'Product analysis failed');
    }
    return res.json();
  },

  // 4. Upload manual reference photos
  async uploadProductImages(formData: FormData): Promise<ProductDetails> {
    const res = await fetch(`${BASE_URL}/products/upload-images`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Image upload failed' }));
      throw new Error(err.detail || 'Image upload failed');
    }
    return res.json();
  },

  // 5. Generate 3D garment from product with size card measurements
  async generate3DFromProduct(params: {
    product_id: string;
    selected_size?: string;
    fit?: string;
    dominant_color_hex?: string;
    include_texture?: boolean;
    measurements?: MeasurementValues;
    unit?: string;
  }): Promise<GenerationJobResponse> {
    const res = await fetch(`${BASE_URL}/products/generate-3d`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: params.product_id,
        selected_size: params.selected_size || 'M',
        fit: params.fit || 'regular',
        dominant_color_hex: params.dominant_color_hex,
        include_texture: params.include_texture ?? true,
        measurements: params.measurements,
        unit: params.unit || 'cm',
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '3D generation failed' }));
      throw new Error(err.detail || '3D generation failed');
    }
    return res.json();
  },

  // --- Common Job & Model Endpoints ---

  // 6. Poll generation job status
  async getJobStatus(jobId: string): Promise<GenerationJobResponse> {
    const res = await fetch(`${BASE_URL}/garments/jobs/${jobId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Job lookup failed' }));
      throw new Error(err.detail || 'Job lookup failed');
    }
    return res.json();
  },

  // 7. Get model metadata
  async getModelMetadata(filename: string): Promise<ModelMetadata> {
    const res = await fetch(`${BASE_URL}/models/${filename}/metadata`);
    if (!res.ok) {
      throw new Error('Failed to load model metadata');
    }
    return res.json();
  },

  // --- Legacy Size Chart (preserved for backwards compatibility if needed) ---
  async uploadSizeChart(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/size-chart/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  async extractSizeChart(chartId: string): Promise<SizeChartData> {
    const res = await fetch(`${BASE_URL}/size-chart/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chart_id: chartId }),
    });
    if (!res.ok) throw new Error('Extraction failed');
    return res.json();
  },

  async generateGarment(config: GarmentConfiguration): Promise<GenerationJobResponse> {
    const res = await fetch(`${BASE_URL}/garments/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Generation failed');
    return res.json();
  },
};
