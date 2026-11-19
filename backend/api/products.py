"""API Router for E-Commerce Product Analysis, Texture Extraction, and 3D Garment Generation."""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from backend.models.schemas import (
    ProductAnalysisRequest,
    ProductDetails,
    Generate3DFromProductRequest,
    GenerationJobResponse
)
from backend.services.product_extraction_service import ProductExtractionService, PRODUCT_CACHE
from backend.services.garment_vision_service import GarmentVisionService
from backend.services.blender_service import BlenderService

router = APIRouter(prefix="/api/products", tags=["E-Commerce Products"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
TEXTURES_DIR = os.path.join(STORAGE_DIR, "textures")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads", "products")
os.makedirs(TEXTURES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.get("/samples")
async def get_sample_products():
    """Returns curated list of sample apparel products for 1-click loading."""
    samples = ProductExtractionService.list_samples()
    return JSONResponse(content={"samples": samples})


@router.get("/samples/{sample_id}")
async def get_sample_details(sample_id: str):
    """Loads detailed sample product information and computer vision attributes."""
    prod = ProductExtractionService.load_sample(sample_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Sample product '{sample_id}' not found.")

    front_img_rel = prod.get("images", {}).get("front", "").lstrip("/")
    front_img_path = os.path.abspath(front_img_rel)
    back_img_rel = prod.get("images", {}).get("back", "").lstrip("/")
    back_img_path = os.path.abspath(back_img_rel) if back_img_rel and os.path.exists(os.path.abspath(back_img_rel)) else None
    detail_img_rel = prod.get("images", {}).get("detail", "").lstrip("/")
    detail_img_path = os.path.abspath(detail_img_rel) if detail_img_rel and os.path.exists(os.path.abspath(detail_img_rel)) else None

    vision = GarmentVisionService.analyze_garment_image(
        image_path=front_img_path,
        product_id=sample_id,
        known_specifications=prod.get("specifications"),
        back_image_path=back_img_path,
        detail_image_path=detail_img_path
    )

    gallery = [
        prod.get("images", {}).get("front"),
        prod.get("images", {}).get("back"),
        prod.get("images", {}).get("detail")
    ]
    gallery = [g for g in gallery if g]

    details = ProductDetails(
        product_id=sample_id,
        title=prod.get("title", ""),
        brand=prod.get("brand", ""),
        category=prod.get("category", "T-Shirts"),
        price=prod.get("price"),
        rating=prod.get("rating"),
        description=prod.get("description", ""),
        specifications=prod.get("specifications", {}),
        primary_image_url=prod.get("images", {}).get("front", ""),
        back_image_url=prod.get("images", {}).get("back"),
        gallery_images=gallery,
        vision_analysis=vision
    )
    return details


@router.post("/analyze", response_model=ProductDetails)
async def analyze_product(request: ProductAnalysisRequest):
    """
    Analyzes an e-commerce product from a Flipkart URL or sample product ID.
    Performs visual detection of base colors, graphic prints, and garment silhouette.
    """
    if request.sample_id:
        return await get_sample_details(request.sample_id)

    if not request.url:
        raise HTTPException(status_code=400, detail="Either 'url' or 'sample_id' must be provided.")

    extracted = await ProductExtractionService.extract_from_url(request.url)
    prod_id = extracted["id"]

    front_img_url = extracted.get("primary_image_url", "")
    front_img_path = ""
    if front_img_url.startswith("/storage/"):
        front_img_path = os.path.abspath(front_img_url.lstrip("/"))
    elif os.path.exists(front_img_url):
        front_img_path = os.path.abspath(front_img_url)

    back_img_url = extracted.get("back_image_url") or ""
    back_img_path = None
    if back_img_url.startswith("/storage/"):
        b_p = os.path.abspath(back_img_url.lstrip("/"))
        if os.path.exists(b_p):
            back_img_path = b_p
    elif back_img_url and os.path.exists(back_img_url):
        back_img_path = os.path.abspath(back_img_url)

    vision = GarmentVisionService.analyze_garment_image(
        image_path=front_img_path,
        product_id=prod_id,
        known_specifications=extracted.get("specifications"),
        back_image_path=back_img_path
    )

    details = ProductDetails(
        product_id=prod_id,
        title=extracted.get("title", "Flipkart Apparel Product"),
        brand=extracted.get("brand", "Brand"),
        category=extracted.get("category", "T-Shirts"),
        price=extracted.get("price"),
        rating=extracted.get("rating"),
        description=extracted.get("description", ""),
        specifications=extracted.get("specifications", {}),
        primary_image_url=front_img_url,
        back_image_url=extracted.get("back_image_url"),
        gallery_images=extracted.get("gallery_images", []),
        vision_analysis=vision
    )
    return details


@router.post("/upload-images", response_model=ProductDetails)
async def upload_product_images(
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    title: str = Form("Custom Reference Garment"),
    brand: str = Form("Custom Upload")
):
    """Handles manual photo upload fallback when automated scraping is blocked."""
    prod_id = f"custom_{uuid.uuid4().hex[:8]}"

    # Save front image
    front_ext = os.path.splitext(front_image.filename)[1] or ".jpg"
    front_filename = f"{prod_id}_front{front_ext}"
    front_path = os.path.join(UPLOADS_DIR, front_filename)

    with open(front_path, "wb") as f:
        content = await front_image.read()
        f.write(content)

    back_filename = None
    if back_image:
        back_ext = os.path.splitext(back_image.filename)[1] or ".jpg"
        back_filename = f"{prod_id}_back{back_ext}"
        back_path = os.path.join(UPLOADS_DIR, back_filename)
        with open(back_path, "wb") as f:
            b_content = await back_image.read()
            f.write(b_content)

    prod = ProductExtractionService.create_custom_upload_product(
        front_filename=front_filename,
        back_filename=back_filename,
        title=title,
        brand=brand
    )

    vision = GarmentVisionService.analyze_garment_image(
        image_path=front_path,
        product_id=prod_id,
        known_specifications=prod.get("specifications"),
        back_image_path=back_path if back_filename else None
    )

    gallery = [f"/storage/uploads/products/{front_filename}"]
    if back_filename:
        gallery.append(f"/storage/uploads/products/{back_filename}")

    return ProductDetails(
        product_id=prod_id,
        title=title,
        brand=brand,
        category="T-Shirts",
        price="Custom Reference",
        rating=5.0,
        description="Manual reference photos uploaded by user.",
        specifications=prod.get("specifications", {}),
        primary_image_url=gallery[0],
        back_image_url=gallery[1] if len(gallery) > 1 else None,
        gallery_images=gallery,
        vision_analysis=vision
    )


@router.post("/generate-3d", response_model=GenerationJobResponse)
async def generate_3d_garment(request: Generate3DFromProductRequest):
    """
    Triggers parametric 3D garment generation in Blender using extracted product design,
    dominant color, and genuine graphic texture.
    """
    job_resp = await BlenderService.generate_from_product(
        product_id=request.product_id,
        selected_size=request.selected_size,
        fit=request.fit,
        dominant_color_hex=request.dominant_color_hex,
        include_texture=request.include_texture,
        measurements=request.measurements,
        unit=request.unit
    )
    return job_resp


@router.get("/textures/{filename}")
async def get_texture_image(filename: str):
    """Serves extracted master texture map PNGs."""
    clean_name = os.path.basename(filename)
    path = os.path.join(TEXTURES_DIR, clean_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Texture not found.")
    return FileResponse(path, media_type="image/png")
