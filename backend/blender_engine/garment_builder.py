"""Master Parametric 3D Garment Generator Dispatcher for Blender Headless Worker.
Dispatches generation to dedicated, high-realism garment builders or the hybrid base mesh lattice deformer:
- Polo T-Shirt: Dedicated Polo builder with folded collar stand, crescent leaf, placket, and 3D buttons
- Basic Plain Crew-Neck T-Shirt: Dedicated Crew builder with hollow round neck, 1x1 rib, and draped sleeves
- Supports Hybrid Base Mesh + Lattice / FFD Scaling when base assets are present
"""
import sys
import os

# Ensure project root is in sys.path for Blender headless execution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import argparse
from typing import Dict, Any

try:
    import bpy
except ImportError:
    bpy = None

from backend.blender_engine.measurement_utils import (
    solve_ellipse_radii, calculate_anatomical_landmarks
)


def build_garment(config: dict, output_glb_path: str) -> dict:
    """
    Main dispatch function called directly or via CLI worker.
    """
    if bpy is None:
        raise RuntimeError("Blender bpy module is required to execute build_garment.")

    garment_type = config.get("garment_type", "basic_crew").lower().strip()
    measurements = config.get("measurements", {})
    selected_size = config.get("selected_size", "M")
    fit = config.get("fit", "regular")

    # Base models paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    storage_base_dir = os.path.join(base_dir, "storage", "base_models")

    crew_base_paths = [
        os.path.join(storage_base_dir, "crew_base.glb"),
        os.path.join(storage_base_dir, "crew_master_base.glb"),
        os.path.join(storage_base_dir, "crew_base.blend")
    ]
    polo_base_paths = [
        os.path.join(storage_base_dir, "polo_base.glb"),
        os.path.join(storage_base_dir, "polo_master_base.glb"),
        os.path.join(storage_base_dir, "polo_base.blend")
    ]

    # Check for master base mesh (Rank 1: Hybrid Base Mesh + Lattice Scaling)
    from backend.blender_engine.lattice_deformer import deform_base_garment

    if garment_type in ["polo", "polo_tshirt"]:
        # Check if polo base mesh exists
        existing_polo_base = next((p for p in polo_base_paths if os.path.exists(p) and os.path.getsize(p) > 1000), None)
        if existing_polo_base:
            try:
                print(f"Using Hybrid Base Mesh + Lattice Scaling with: {existing_polo_base}")
                meta = deform_base_garment(existing_polo_base, measurements, config, output_glb_path)
                meta["selected_size"] = selected_size
                meta["fit"] = fit
                return meta
            except Exception as e:
                print(f"Lattice deformation warning: {e}. Falling back to dedicated polo builder.")

        from backend.blender_engine.polo_geometry_builder import build_polo_garment
        meta = build_polo_garment(config, output_glb_path)
        meta["selected_size"] = selected_size
        meta["fit"] = fit
        return meta

    else:
        # Basic Plain Crew-Neck T-Shirt (or regular_tshirt)
        existing_crew_base = next((p for p in crew_base_paths if os.path.exists(p) and os.path.getsize(p) > 1000), None)
        if existing_crew_base:
            try:
                print(f"Using Hybrid Base Mesh + Lattice Scaling with: {existing_crew_base}")
                meta = deform_base_garment(existing_crew_base, measurements, config, output_glb_path)
                meta["selected_size"] = selected_size
                meta["fit"] = fit
                return meta
            except Exception as e:
                print(f"Lattice deformation warning: {e}. Falling back to dedicated crew builder.")

        from backend.blender_engine.crew_geometry_builder import build_crew_garment
        meta = build_crew_garment(config, output_glb_path)
        meta["selected_size"] = selected_size
        meta["fit"] = fit
        return meta


def main():
    parser = argparse.ArgumentParser(description="Blender Parametric Garment Generator")
    parser.add_argument("--config", type=str, help="Path to JSON configuration file")
    parser.add_argument("--json", type=str, help="JSON configuration string")
    parser.add_argument("--output", type=str, required=True, help="Path to output GLB file")

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = json.load(f)
    elif args.json:
        config = json.loads(args.json)
    else:
        raise ValueError("Either --config or --json must be specified.")

    meta = build_garment(config, args.output)
    print("GENERATION_METADATA:" + json.dumps(meta))


if __name__ == "__main__" and bpy is not None:
    main()
