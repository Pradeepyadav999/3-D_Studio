"""Mesh integrity and requested dimension checks."""
import numpy as np
from .stitch import edge_incidence


def validate_mesh(vertices, faces):
    if not np.isfinite(vertices).all(): raise ValueError("mesh contains NaN or infinite vertices")
    tri = vertices[faces]
    areas = np.linalg.norm(np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]),axis=1)/2
    if np.any(areas <= 1e-12): raise ValueError("mesh contains zero-area triangles")
    if len(np.unique(np.round(vertices,12),axis=0)) != len(vertices): raise ValueError("mesh contains duplicate vertices")
    counts = edge_incidence(faces)
    if any(n > 2 for n in counts.values()): raise ValueError("mesh has non-manifold edges")
    boundary = sum(n == 1 for n in counts.values())
    return {"vertices":len(vertices),"faces":len(faces),"boundary_edges":boundary,"closed":boundary==0}


def validate_dimensions(spec, vertices):
    span = float(vertices[:,0].max()-vertices[:,0].min())
    length = float(vertices[:,2].max()-vertices[:,2].min())
    return {"requested_cm":{"chest":spec.chest_circumference_cm,"shoulder":spec.shoulder.cm(),"length":spec.length.cm()},
            "actual_cm":{"chest_cross_section":None,"shoulder":span,"length":length},
            "derived":{"panel_depth_cm":"estimated from chest circumference"}}

