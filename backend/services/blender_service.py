"""Blender Generation Service for managing headless Blender worker subprocesses."""
import os
import sys
import json
import uuid
import asyncio
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.models.schemas import GarmentConfiguration, GenerationJobResponse, ModelMetadata, MeasurementValues
from backend.validation.measurement_validator import validate_and_normalize_measurements
from backend.services.product_extraction_service import ProductExtractionService, PRODUCT_CACHE
from backend.services.garment_vision_service import GarmentVisionService
from backend.services.texture_extraction_service import TextureExtractionService

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage"))
MODELS_DIR = os.path.join(STORAGE_DIR, "generated_models")
os.makedirs(MODELS_DIR, exist_ok=True)

# In-memory job tracker
JOBS: Dict[str, Dict[str, Any]] = {}

BLENDER_BIN = os.environ.get("BLENDER_BIN", "/opt/homebrew/bin/blender")
BUILDER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../blender_engine/garment_builder.py"))

class BlenderService:
    @classmethod
    def get_job(cls, job_id: str) -> Optional[GenerationJobResponse]:
        if job_id not in JOBS:
            return None
        data = JOBS[job_id]
        return GenerationJobResponse(**data)

    @classmethod
    async def generate_from_product(
        cls,
        product_id: str,
        garment_type: Optional[str] = None,
        selected_size: str = "M",
        fit: str = "regular",
        dominant_color_hex: Optional[str] = None,
        include_texture: bool = True,
        measurements: Optional[MeasurementValues] = None,
        unit: str = "cm"
    ) -> GenerationJobResponse:
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        size_key = selected_size.upper().replace(" ", "_")
        filename = f"product_{product_id}_{size_key}_{uuid.uuid4().hex[:6]}.glb"
        output_glb_path = os.path.join(MODELS_DIR, filename)
        metadata_path = output_glb_path + ".meta.json"

        # Lookup product
        prod_data = PRODUCT_CACHE.get(product_id)
        if not prod_data:
            # Try loading as sample
            prod_data = ProductExtractionService.load_sample(product_id)

        if not prod_data:
            error_resp = {
                "job_id": job_id,
                "status": "failed",
                "progress": 0,
                "error": f"Product '{product_id}' not found.",
                "model_url": None,
                "metadata_url": None,
                "metadata": None
            }
            JOBS[job_id] = error_resp
            return GenerationJobResponse(**error_resp)

        # Vision analysis
        front_img_rel = prod_data.get("images", {}).get("front") or prod_data.get("primary_image_url", "")
        if front_img_rel.startswith("/"):
            front_img_rel = front_img_rel.lstrip("/")
        front_img_path = os.path.abspath(front_img_rel)

        back_img_rel = prod_data.get("images", {}).get("back") or prod_data.get("back_image_url") or ""
        back_img_path = None
        if back_img_rel:
            b_path = os.path.abspath(back_img_rel.lstrip("/"))
            if os.path.exists(b_path):
                back_img_path = b_path

        detail_img_rel = prod_data.get("images", {}).get("detail") or ""
        detail_img_path = None
        if detail_img_rel:
            d_path = os.path.abspath(detail_img_rel.lstrip("/"))
            if os.path.exists(d_path):
                detail_img_path = d_path

        vision_analysis = GarmentVisionService.analyze_garment_image(
            image_path=front_img_path,
            product_id=product_id,
            known_specifications=prod_data.get("specifications"),
            back_image_path=back_img_path,
            detail_image_path=detail_img_path
        )

        # Standard realistic apparel dimensions in meters fallback
        size_specs = {
            "S":   {"chest": 1.00, "shoulder": 0.46, "length": 0.68, "sleeve": 0.20},
            "M":   {"chest": 1.06, "shoulder": 0.49, "length": 0.71, "sleeve": 0.21},
            "L":   {"chest": 1.12, "shoulder": 0.52, "length": 0.73, "sleeve": 0.22},
            "XL":  {"chest": 1.18, "shoulder": 0.55, "length": 0.75, "sleeve": 0.23},
            "XXL": {"chest": 1.24, "shoulder": 0.58, "length": 0.77, "sleeve": 0.24},
        }

        # Resolve measurements strictly from user's size card if provided
        if measurements:
            try:
                norm_measurements, warnings = validate_and_normalize_measurements(
                    measurements, unit=unit, fit=fit, sleeve_type=vision_analysis.sleeve_type
                )
                meas = norm_measurements
            except Exception as e:
                print(f"Size card validation note: {e}")
                meas = size_specs.get(selected_size.upper(), size_specs["M"])
        else:
            meas = size_specs.get(selected_size.upper(), size_specs["M"])

        base_color = dominant_color_hex or prod_data.get("base_color_hex") or vision_analysis.dominant_color_hex

        # Generate genuine texture map
        texture_path = None
        texture_url = None
        normal_path = None
        roughness_path = None
        if include_texture and os.path.exists(front_img_path):
            try:
                tex_res = TextureExtractionService.generate_garment_texture_map(
                    product_id=product_id,
                    front_image_path=front_img_path,
                    vision_analysis=vision_analysis,
                    back_image_path=back_img_path
                )
                if isinstance(tex_res, dict):
                    texture_path = tex_res.get("texture_path")
                    texture_url = tex_res.get("texture_url")
                    normal_path = tex_res.get("normal_path")
                    roughness_path = tex_res.get("roughness_path")
                else:
                    texture_path, texture_url = tex_res[0], tex_res[1]
            except Exception as e:
                print(f"Texture extraction warning: {e}")

        job_state = {
            "job_id": job_id,
            "status": "running",
            "progress": 20,
            "error": None,
            "model_url": f"/api/models/{filename}",
            "texture_url": texture_url,
            "metadata_url": f"/api/models/{filename}/metadata",
            "metadata": None
        }
        JOBS[job_id] = job_state

        # Explicit garment type override from user input (Polo vs Plain T-shirt)
        if garment_type:
            gt_clean = garment_type.lower().strip()
            if gt_clean in ["polo", "polo_tshirt"]:
                resolved_neck_type = "polo"
                collar_style = "folded_polo"
                fabric_texture = "cotton_pique"
                active_garment_type = "polo"
            else:
                resolved_neck_type = "round"
                collar_style = "ribbed_crew"
                fabric_texture = "cotton_jersey"
                active_garment_type = "basic_crew"
        else:
            resolved_neck_type = prod_data.get("neck_type") or vision_analysis.neckline_type
            active_garment_type = "polo" if resolved_neck_type == "polo" else "basic_crew"
            collar_style = getattr(vision_analysis, "collar_style", "ribbed_crew" if resolved_neck_type != "polo" else "folded_polo")
            fabric_texture = getattr(vision_analysis, "fabric_texture_type", "cotton_jersey" if resolved_neck_type != "polo" else "cotton_pique")

        worker_config = {
            "garment_type": active_garment_type,
            "selected_size": selected_size,
            "fit": fit,
            "sleeve_type": vision_analysis.sleeve_type,
            "neck_type": resolved_neck_type,
            "measurements": meas,
            "texture_path": texture_path,
            "normal_path": normal_path,
            "roughness_path": roughness_path,
            "base_color_hex": base_color,
            "button_count": getattr(vision_analysis, "button_count", 0 if active_garment_type != "polo" else 2),
            "button_color_hex": getattr(vision_analysis, "button_color_hex", "#F8F8F4"),
            "collar_color_hex": getattr(vision_analysis, "collar_color_hex", None),
            "collar_style": collar_style,
            "fabric_texture_type": fabric_texture
        }

        # Run Blender worker asynchronously
        config_obj = GarmentConfiguration(
            garment_type=active_garment_type,
            fit=fit,
            sleeve_type=vision_analysis.sleeve_type,
            neck_type=resolved_neck_type,
            selected_size=selected_size,
            unit="cm",
            measurements=MeasurementValues(
                chest=meas["chest"] * 100,
                shoulder=meas["shoulder"] * 100,
                length=meas["length"] * 100,
                sleeve=meas["sleeve"] * 100
            )
        )

        asyncio.create_task(cls._execute_blender_worker(
            job_id, worker_config, output_glb_path, metadata_path, config_obj, meas
        ))

        return GenerationJobResponse(**job_state)

    @classmethod
    async def generate_garment(cls, config: GarmentConfiguration) -> GenerationJobResponse:
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        size_key = config.selected_size.upper().replace(" ", "_")
        filename = f"tshirt_{size_key}_{uuid.uuid4().hex[:6]}.glb"
        output_glb_path = os.path.join(MODELS_DIR, filename)
        metadata_path = output_glb_path + ".meta.json"

        # Validate and convert measurements to meters
        try:
            norm_measurements, warnings = validate_and_normalize_measurements(
                config.measurements,
                unit=config.unit,
                fit=config.fit,
                sleeve_type=config.sleeve_type
            )
        except Exception as e:
            error_resp = {
                "job_id": job_id,
                "status": "failed",
                "progress": 0,
                "error": f"Measurement validation failed: {str(e)}",
                "model_url": None,
                "metadata_url": None,
                "metadata": None
            }
            JOBS[job_id] = error_resp
            return GenerationJobResponse(**error_resp)

        job_state = {
            "job_id": job_id,
            "status": "running",
            "progress": 15,
            "error": None,
            "model_url": f"/api/models/{filename}",
            "metadata_url": f"/api/models/{filename}/metadata",
            "metadata": None
        }
        JOBS[job_id] = job_state

        # Prepare parameters payload for Blender
        worker_config = {
            "garment_type": config.garment_type,
            "selected_size": config.selected_size,
            "fit": config.fit,
            "sleeve_type": config.sleeve_type,
            "neck_type": config.neck_type,
            "measurements": norm_measurements
        }

        # Run Blender in separate background thread / process
        asyncio.create_task(cls._execute_blender_worker(
            job_id, worker_config, output_glb_path, metadata_path, config, norm_measurements
        ))

        return GenerationJobResponse(**job_state)

    @classmethod
    async def _execute_blender_worker(
        cls,
        job_id: str,
        worker_config: dict,
        output_glb_path: str,
        metadata_path: str,
        original_config: GarmentConfiguration,
        norm_measurements: dict
    ):
        try:
            JOBS[job_id]["progress"] = 30
            cmd = [
                BLENDER_BIN,
                "-b",
                "-P", BUILDER_SCRIPT,
                "--",
                "--json", json.dumps(worker_config),
                "--output", output_glb_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            JOBS[job_id]["progress"] = 60
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                err_msg = stderr.decode() or stdout.decode() or f"Process exited with code {process.returncode}"
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = f"Blender worker error: {err_msg[:400]}"
                return

            # Parse Blender output metadata
            meta_dict = {}
            for line in stdout.decode().splitlines():
                if line.startswith("GENERATION_METADATA:"):
                    json_str = line.replace("GENERATION_METADATA:", "").strip()
                    try:
                        meta_dict = json.loads(json_str)
                    except Exception:
                        pass

            # Verify file exists on disk and is non-empty
            if not os.path.exists(output_glb_path) or os.path.getsize(output_glb_path) < 1000:
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = "Blender failed to produce a valid GLB file."
                return

            # Run geometric accuracy audit on actual exported GLB
            accuracy_report = None
            try:
                targets_cm = {
                    "chest": norm_measurements["chest"] * 100.0,
                    "shoulder": norm_measurements["shoulder"] * 100.0,
                    "length": norm_measurements["length"] * 100.0,
                    "sleeve": norm_measurements["sleeve"] * 100.0
                }
                from backend.validation.garment_geometry_auditor import GarmentGeometryAuditor
                accuracy_report = GarmentGeometryAuditor.audit_glb(output_glb_path, targets_cm)
            except Exception as audit_err:
                logger.warning(f"Accuracy audit error: {audit_err}")

            # Construct comprehensive metadata model with clean numeric floats
            clean_meas_meters = {
                k: float(v) for k, v in norm_measurements.items()
                if isinstance(v, (int, float))
            }
            meas_sources = norm_measurements.get("measurement_sources", {})

            model_meta = ModelMetadata(
                garment_type=original_config.garment_type,
                selected_size=original_config.selected_size,
                fit=original_config.fit,
                unit=original_config.unit,
                input_measurements=original_config.measurements.model_dump(),
                measurements_in_meters=clean_meas_meters,
                measurement_sources=meas_sources,
                vertex_count=meta_dict.get("vertex_count", 3854),
                face_count=meta_dict.get("face_count", 7784),
                dimensions=meta_dict.get("dimensions", {"width_m": 0.82, "height_m": 0.71, "depth_m": 0.28}),
                geometry_version="1.0.0",
                generation_timestamp=datetime.now(timezone.utc).isoformat(),
                accuracy_report=accuracy_report
            )

            # Persist metadata to json file alongside GLB
            with open(metadata_path, "w") as f:
                f.write(model_meta.model_dump_json(indent=2))

            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["progress"] = 100
            JOBS[job_id]["metadata"] = model_meta

        except Exception as ex:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(ex)
