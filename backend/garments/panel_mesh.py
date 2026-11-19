"""Polygon triangulation and front/back surface construction."""
from dataclasses import dataclass
import math
import numpy as np
from scipy.spatial import Delaunay
from .pattern import Panel


@dataclass
class Mesh:
    vertices: np.ndarray
    faces: np.ndarray
    component_names: tuple[str, ...]


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _inside(p, poly):
    x, y = p
    inside = False
    j = len(poly)-1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and x < (xj-xi)*(y-yi)/(yj-yi+1e-30)+xi:
            inside = not inside
        j = i
    return inside


def triangulate_panel(panel: Panel, spacing_cm: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    poly = np.asarray(panel.outline, dtype=float)
    if not np.isfinite(poly).all() or len(poly) < 4:
        raise ValueError(f"{panel.name}: invalid outline")
    # Sample each boundary edge evenly, retaining exact shared-edge positions.
    boundary = []
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        n = max(1, int(math.ceil(np.linalg.norm(b-a)/spacing_cm)))
        boundary.extend(a+(b-a)*(i/n) for i in range(n))
    pts = list(boundary)
    xmin,ymin = poly.min(axis=0); xmax,ymax = poly.max(axis=0)
    ys = np.arange(ymin+spacing_cm, ymax, spacing_cm)
    xs = np.arange(xmin+spacing_cm, xmax, spacing_cm)
    pts.extend((x,y) for y in ys for x in xs if _inside((x,y), poly))
    pts = np.asarray(pts, dtype=float)
    tri = Delaunay(pts).simplices
    keep = []
    for face in tri:
        c = pts[face].mean(axis=0)
        if _inside(c, poly) and all(_inside((pts[face[i]]*.25+pts[face[(i+1)%3]]*.75), poly) for i in range(3)):
            if abs(_cross(*pts[face])) > 1e-8:
                keep.append(face)
    if not keep:
        raise ValueError(f"{panel.name}: triangulation produced no interior faces")
    return pts, np.asarray(keep, dtype=np.int64)


def make_shell_mesh(panels: tuple[Panel, ...], depth_cm: float, spacing_cm: float = 2.0) -> Mesh:
    vertices, faces = [], []
    for panel in panels:
        pts, tris = triangulate_panel(panel, spacing_cm)
        base = len(vertices)
        y = -depth_cm/2 if panel.side == "front" else depth_cm/2
        vertices.extend((float(x), y, float(z)) for x,z in pts)
        # Front faces point +Y, back faces point -Y.
        for a,b,c in tris:
            if panel.side == "front": faces.append((base+a,base+c,base+b))
            else: faces.append((base+a,base+b,base+c))
    return Mesh(np.asarray(vertices,dtype=float),np.asarray(faces,dtype=np.int64),tuple(p.name for p in panels))

