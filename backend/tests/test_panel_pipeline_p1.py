import math
import numpy as np
import pytest
from backend.garments.spec import GarmentSpec, Measure
from backend.garments.pattern import crew_body_panels
from backend.garments.panel_mesh import make_shell_mesh
from backend.garments.stitch import weld_vertices
from backend.garments.validate import validate_mesh


def make_spec(chest, unit='in', definition='circumference'):
    return GarmentSpec('crew_neck', Measure(chest,unit,'user',definition), Measure(17,unit,'user','seam_to_seam'), Measure(28,unit,'user','HPS_to_hem'))


def test_units_and_explicit_flat_width_equivalence():
    assert math.isclose(make_spec(40).chest_circumference_cm, make_spec(20,definition='flat_width').chest_circumference_cm)
    assert math.isclose(Measure(1,'in').cm(),2.54)


def test_range_validation_requires_chest_definition():
    with pytest.raises(ValueError,match='definition'):
        GarmentSpec('crew_neck',Measure(40,'in'),Measure(17,'in'),Measure(28,'in'))
    with pytest.raises(ValueError,match='shoulder'):
        GarmentSpec('crew_neck',Measure(40,'in','user','circumference'),Measure(5,'in'),Measure(28,'in'))


def test_p1_panels_are_finite_and_have_nonzero_faces():
    spec=make_spec(40)
    panels=crew_body_panels(spec)
    mesh=make_shell_mesh(panels,depth_cm=19,spacing_cm=2.5)
    verts,faces=weld_vertices(mesh.vertices,mesh.faces)
    report=validate_mesh(verts,faces)
    assert len(verts)>100 and len(faces)>100
    assert report['boundary_edges']>0  # P1 body surfaces retain neck, armhole and hem openings.
    assert np.isfinite(verts).all()
    assert np.all(np.linalg.norm(np.cross(verts[faces][:,1]-verts[faces][:,0],verts[faces][:,2]-verts[faces][:,0]),axis=1)>1e-12)
