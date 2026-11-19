"""Pydantic schemas for 3D Garment Studio."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class MeasurementValues(BaseModel):
    chest: float = Field(..., description="Chest circumference in specified unit")
    shoulder: float = Field(..., description="Shoulder width from edge to edge in specified unit")
    length: float = Field(..., description="Garment length from high point shoulder to hem")
    sleeve: float = Field(..., description="Sleeve length from shoulder seam to sleeve cuff")
    waist: Optional[float] = Field(None, description="Optional waist circumference")
    hem: Optional[float] = Field(None, description="Optional bottom hem circumference")
    neck: Optional[float] = Field(None, description="Optional neck circumference or collar width")
    sleeve_opening: Optional[float] = Field(None, description="Optional sleeve cuff circumference")

class SizeChartData(BaseModel):
    chart_id: str
    unit: str = Field(default="cm", description="Measurement unit: cm or inch")
    measurement_type: str = Field(default="garment", description="'garment' or 'body'")
    confidence: Optional[float] = Field(default=1.0, description="Overall OCR extraction confidence (0-1)")
    sizes: Dict[str, MeasurementValues] = Field(default_factory=dict)
    raw_ocr_text: Optional[str] = None
    cell_confidences: Optional[Dict[str, Dict[str, float]]] = None
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UploadResponse(BaseModel):
    chart_id: str
    filename: str
    file_url: str
    content_type: str
    size_bytes: int

class ExtractionRequest(BaseModel):
    chart_id: str

class GarmentConfiguration(BaseModel):
    garment_type: str = Field(default="regular_tshirt", description="Garment style: regular_tshirt")
    fit: str = Field(default="regular", description="Fit profile: regular, slim, relaxed")
    sleeve_type: str = Field(default="short", description="Sleeve type: short, long")
    neck_type: str = Field(default="round", description="Neckline type: round, v_neck")
    selected_size: str = Field(default="L", description="Selected size key, e.g., S, M, L, XL, XXL")
    unit: str = Field(default="cm", description="Measurement unit: cm or inch")
    measurements: MeasurementValues

class ModelMetadata(BaseModel):
    garment_type: str
    selected_size: str
    fit: str
    unit: str
    input_measurements: Dict[str, Optional[float]]
    measurements_in_meters: Dict[str, Optional[float]]
    vertex_count: int
    face_count: int
    dimensions: Dict[str, float]  # width_m, height_m, depth_m
    geometry_version: str = "1.0.0"
    generation_timestamp: str
    accuracy_report: Optional[Dict[str, Any]] = None

class GenerationJobResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    job_id: str
    status: str = Field(..., description="pending, running, completed, failed")
    progress: int = Field(default=0, description="Progress percentage 0-100")
    model_url: Optional[str] = None
    texture_url: Optional[str] = None
    metadata_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[ModelMetadata] = None


# --- AI E-Commerce Product to 3D Garment Schemas ---

class GraphicAnalysis(BaseModel):
    detected: bool = Field(default=False, description="Whether a graphic print, emblem, or logo was detected")
    placement: str = Field(default="none", description="Chest Center, Left Chest, Full Front, etc.")
    bounding_box: Optional[List[int]] = Field(default=None, description="[x_min, y_min, x_max, y_max] in image pixels")
    badge_preview_url: Optional[str] = Field(default=None, description="URL of cropped print preview")
    description: Optional[str] = Field(default=None, description="Visual description of graphic print")


class GarmentVisionAnalysis(BaseModel):
    dominant_color_hex: str = Field(default="#1C1C1E", description="Primary garment base color in hex")
    dominant_color_name: str = Field(default="Black", description="Human-readable color name")
    secondary_colors: List[str] = Field(default_factory=list, description="Accent and secondary colors in hex")
    neckline_type: str = Field(default="round", description="round (crew neck), v_neck, polo")
    sleeve_type: str = Field(default="short", description="short, long, sleeveless")
    silhouette: str = Field(default="regular", description="regular, slim, relaxed")
    pattern_type: str = Field(default="solid", description="solid, graphic_print, chest_badge, patterned")
    front_cutout_url: Optional[str] = Field(default=None, description="URL of segmented transparent front garment cutout")
    back_cutout_url: Optional[str] = Field(default=None, description="URL of segmented transparent back garment cutout")
    back_status: str = Field(default="plain", description="extracted, plain, missing_reference")
    button_count: int = Field(default=0, description="Detected or specified button count (e.g. 2 or 3 for polo, 0 for crew/v-neck)")
    button_color_hex: str = Field(default="#F8F8F4", description="Color of buttons in hex")
    collar_color_hex: Optional[str] = Field(default=None, description="Contrast collar color in hex if distinct from dominant body")
    placket_length_cm: float = Field(default=0.0, description="Length of front placket in cm")
    placket_width_cm: float = Field(default=0.0, description="Width of front placket in cm")
    collar_style: str = Field(default="ribbed_crew", description="folded_polo, ribbed_crew, ribbed_v")
    fabric_texture_type: str = Field(default="cotton_jersey", description="cotton_jersey, cotton_pique, ribbed_knit")
    normal_map_url: Optional[str] = Field(default=None, description="URL of generated PBR normal map")
    roughness_map_url: Optional[str] = Field(default=None, description="URL of generated PBR roughness map")
    graphic: GraphicAnalysis = Field(default_factory=GraphicAnalysis, description="Front chest graphic or print")
    back_graphic: Optional[GraphicAnalysis] = Field(default=None, description="Back panel graphic, print, or typography")
    sleeve_graphic: Optional[GraphicAnalysis] = Field(default=None, description="Sleeve badge, stripe, or print")
    fabric_appearance: str = Field(default="100% Combed Cotton Single Jersey", description="Detected fabric texture")
    confidence_score: float = Field(default=0.95, description="AI classification confidence score 0-1")


class ProductDetails(BaseModel):
    product_id: str
    title: str
    brand: str
    category: str
    price: Optional[str] = None
    rating: Optional[float] = None
    description: str
    specifications: Dict[str, str] = Field(default_factory=dict)
    primary_image_url: str
    back_image_url: Optional[str] = None
    gallery_images: List[str] = Field(default_factory=list)
    vision_analysis: GarmentVisionAnalysis


class ProductAnalysisRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="Live Flipkart product URL")
    sample_id: Optional[str] = Field(default=None, description="Sample product ID (e.g. fk_graphic_crew_black)")


class Generate3DFromProductRequest(BaseModel):
    product_id: str
    selected_size: str = Field(default="M", description="Garment size: S, M, L, XL, XXL")
    fit: str = Field(default="regular", description="Fit profile: regular, slim, relaxed")
    dominant_color_hex: Optional[str] = None
    include_texture: bool = True
    measurements: Optional[MeasurementValues] = Field(default=None, description="Exact size card measurements provided by user")
    unit: str = Field(default="cm", description="Measurement unit: cm or inch")

