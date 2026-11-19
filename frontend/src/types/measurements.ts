export type ChestMeasurementType = 'circumference' | 'flat_width';

export interface MeasurementValues {
  chest: number;
  chest_measurement_type?: ChestMeasurementType;
  shoulder: number;
  length: number;
  sleeve?: number | null;
  waist?: number | null;
  hem?: number | null;
  neck?: number | null;
  sleeve_opening?: number | null;
  measurement_sources?: Record<string, string>;
}

export interface SizeChartData {
  chart_id: string;
  unit: string;
  measurement_type: string;
  confidence: number;
  sizes: Record<string, MeasurementValues>;
  raw_ocr_text?: string;
  cell_confidences?: Record<string, Record<string, number>>;
  warnings?: string[];
  created_at?: string;
}

export interface UploadResponse {
  chart_id: string;
  filename: string;
  file_url: string;
  content_type: string;
  size_bytes: number;
}
