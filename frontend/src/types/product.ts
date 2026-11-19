export interface GraphicAnalysis {
  detected: boolean;
  placement: string;
  bounding_box?: number[] | null;
  badge_preview_url?: string | null;
  description?: string | null;
}

export interface GarmentVisionAnalysis {
  dominant_color_hex: string;
  dominant_color_name: string;
  secondary_colors: string[];
  neckline_type: string;
  sleeve_type: string;
  silhouette: string;
  pattern_type?: string;
  front_cutout_url?: string | null;
  back_cutout_url?: string | null;
  back_status?: string;
  button_count?: number;
  button_color_hex?: string;
  placket_length_cm?: number;
  placket_width_cm?: number;
  collar_style?: string;
  fabric_texture_type?: string;
  normal_map_url?: string | null;
  roughness_map_url?: string | null;
  graphic: GraphicAnalysis;
  back_graphic?: GraphicAnalysis | null;
  sleeve_graphic?: GraphicAnalysis | null;
  fabric_appearance: string;
  confidence_score: number;
}

export interface ProductDetails {
  product_id: string;
  title: string;
  brand: string;
  category: string;
  price?: string | null;
  rating?: number | null;
  description: string;
  specifications: Record<string, string>;
  primary_image_url: string;
  back_image_url?: string | null;
  gallery_images: string[];
  vision_analysis: GarmentVisionAnalysis;
}

export interface SampleProductSummary {
  id: string;
  title: string;
  brand: string;
  price: string;
  rating: number;
  base_color_hex: string;
  color_name: string;
  thumbnail: string;
  graphic_description: string;
}
