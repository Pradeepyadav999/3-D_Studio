"""Parametric 3D T-shirt & Polo Generator for Blender Headless Worker.
Phase 3: Measurement-Driven Deformation Engine.
Loads master base templates (Plain Crew-Neck & Polo T-Shirt) and deforms them
strictly driven by 3 user measurements:
  1. Chest Circumference
  2. Shoulder Width
  3. Garment Length
"""
import sys
import os
import json
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
for p in [current_dir, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import bpy
except ImportError:
    bpy = None

try:
    from backend.blender_engine.garment_deformer import generate_measurement_driven_garment
except ImportError:
    from garment_deformer import generate_measurement_driven_garment


def build_garment(config: dict, output_glb_path: str) -> dict:
    """
    Builds the deformed garment mesh from user measurements and exports GLB.
    """
    if bpy is None:
        raise RuntimeError("Blender bpy module is required to execute build_garment.")
    return generate_measurement_driven_garment(config, output_glb_path)


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
