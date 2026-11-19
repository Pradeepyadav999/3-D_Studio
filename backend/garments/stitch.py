"""Seam welding and topology checks."""
from collections import Counter
import numpy as np


def weld_vertices(vertices: np.ndarray, faces: np.ndarray, tolerance: float = 1e-8):
    key = np.round(vertices/tolerance).astype(np.int64)
    _, inverse = np.unique(key, axis=0, return_inverse=True)
    welded = np.zeros((inverse.max()+1,3), dtype=float)
    counts = np.bincount(inverse)
    np.add.at(welded,inverse,vertices)
    welded /= counts[:,None]
    return welded, inverse[faces]


def edge_incidence(faces: np.ndarray):
    edges = Counter()
    for tri in faces:
        for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            edges[tuple(sorted((int(a),int(b))))] += 1
    return edges

