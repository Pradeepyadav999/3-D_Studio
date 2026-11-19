"""P1 crew body generation entry point."""
from .spec import GarmentSpec, Measure
from .pattern import crew_body_panels
from .inflate import panel_depth_m
from .panel_mesh import make_shell_mesh
from .stitch import weld_vertices
from .validate import validate_mesh, validate_dimensions
from .export_glb import export_glb


def build_crew_body(config, output_path):
    m=config['measurements']; unit=config.get('unit','cm')
    chest_def=m.get('chest_measurement_type','circumference')
    spec=GarmentSpec('crew_neck',Measure(float(m['chest']),unit,'user',chest_def),Measure(float(m['shoulder']),unit,'user','seam_to_seam'),Measure(float(m['length']),unit,'user','HPS_to_hem'))
    panels=crew_body_panels(spec)
    depth_cm=panel_depth_m(spec.chest_circumference_cm)*100
    mesh=make_shell_mesh(panels,depth_cm)
    verts,faces=weld_vertices(mesh.vertices,mesh.faces)
    # GLB uses metres. The P1 construction is two disconnected front/back surfaces;
    # seam closure and volume are intentionally built in subsequent pipeline work.
    report=validate_mesh(verts,faces)
    dimensions=validate_dimensions(spec,verts)
    export_glb(output_path,verts/100.0,faces)
    return {"vertex_count":len(verts),"face_count":len(faces),"dimensions":{"width_m":float((verts[:,0].max()-verts[:,0].min())/100),"height_m":float((verts[:,2].max()-verts[:,2].min())/100),"depth_m":depth_cm/100},"mesh_validation":report,"measurement_report":dimensions,"component_names":["CrewBody"],"units":"metres"}

