import { MeasurementValues } from './measurements';

export type GarmentType = 'basic_crew' | 'polo';
export type FitType = 'regular' | 'slim' | 'relaxed';
export type SleeveType = 'short' | 'long';
export type NeckType = 'round' | 'v_neck';
export type ShadingMode = 'textured' | 'solid' | 'wireframe' | 'solid_wireframe';
export type ViewPreset = 'perspective' | 'front' | 'back' | 'left' | 'right' | 'top';

export interface GarmentConfiguration {
  garment_type: string;
  fit: FitType;
  sleeve_type: SleeveType;
  neck_type: NeckType;
  selected_size: string;
  unit: string;
  measurements: MeasurementValues;
}

export interface ModelMetadata {
  garment_type: string;
  selected_size: string;
  fit: string;
  unit: string;
  input_measurements: Record<string, number | null>;
  measurements_in_meters: Record<string, number>;
  vertex_count: number;
  face_count: number;
  dimensions: {
    width_m: number;
    height_m: number;
    depth_m: number;
  };
  geometry_version: string;
  generation_timestamp: string;
  accuracy_report?: {
    chest_circumference: { input_target_cm: number; actual_glb_cm: number; difference_cm: number; tolerance_cm: number; status: string };
    shoulder_width: { input_target_cm: number; actual_glb_cm: number; difference_cm: number; tolerance_cm: number; status: string };
    body_length: { input_target_cm: number; actual_glb_cm: number; difference_cm: number; tolerance_cm: number; status: string };
    sleeve_length: { input_target_cm: number; actual_glb_cm: number; difference_cm: number; tolerance_cm: number; status: string };
    torso_depth: { actual_glb_cm: number };
    overall_dimensions: { width_cm: number; height_cm: number; depth_cm: number };
    mesh_topology: { vertex_count: number; polygon_count: number; topology: string };
  };
}

export interface GenerationJobResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  model_url?: string;
  texture_url?: string;
  metadata_url?: string;
  error?: string;
  metadata?: ModelMetadata;
}
