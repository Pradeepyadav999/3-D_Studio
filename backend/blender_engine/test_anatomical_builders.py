"""Test script to verify anatomical garment mesh construction with Pacdora-matched contours:
- Natural shoulder depth (12-14 cm across deltoid instead of 2.2 cm razor-edge)
- Pectoral front-swell and thoracic back-curve
- Relaxed A-pose sleeves (44° drape, 14° forward pitch)
- Open collar with natural cloth thickness
- Top-front elevated mockup camera (38° elevation)
"""
import sys
import os

# Add project root to sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root not in sys.path:
    sys.path.insert(0, root)

import bpy
import bmesh
import math
from mathutils import Vector

print("Blender version:", bpy.app.version_string)
