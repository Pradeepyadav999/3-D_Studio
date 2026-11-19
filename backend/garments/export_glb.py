"""GLB export for the Python panel pipeline."""
import json
import os
import struct
import numpy as np


def export_glb(path, vertices_m, faces, name="CrewBody"):
    # Minimal glTF 2.0 binary writer: positions, indices, one neutral material.
    pos = np.asarray(vertices_m,dtype="<f4").tobytes()
    idx = np.asarray(faces,dtype="<u4").reshape(-1).tobytes()
    while len(pos)%4: pos += b'\0'
    pos_len=len(pos); blob=pos+idx
    doc={"asset":{"version":"2.0","generator":"Garment Studio panel pipeline"},
      "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":name}],
      "meshes":[{"name":name,"primitives":[{"attributes":{"POSITION":0},"indices":1,"material":0,"mode":4}]}],
      "materials":[{"name":"Neutral Fabric","pbrMetallicRoughness":{"baseColorFactor":[0.78,0.80,0.83,1],"metallicFactor":0,"roughnessFactor":0.82},"doubleSided":True}],
      "buffers":[{"byteLength":len(blob)}],"bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":pos_len,"target":34962},{"buffer":0,"byteOffset":pos_len,"byteLength":len(idx),"target":34963}],
      "accessors":[{"bufferView":0,"componentType":5126,"count":len(vertices_m),"type":"VEC3","min":np.min(vertices_m,axis=0).tolist(),"max":np.max(vertices_m,axis=0).tolist()},{"bufferView":1,"componentType":5125,"count":faces.size,"type":"SCALAR"}]}
    js=json.dumps(doc,separators=(',',':')).encode(); js+=b' '*((-len(js))%4)
    blob+=b'\0'*((-len(blob))%4)
    total=12+8+len(js)+8+len(blob)
    os.makedirs(os.path.dirname(os.path.abspath(path)),exist_ok=True)
    with open(path,'wb') as f:
        f.write(struct.pack('<4sII',b'glTF',2,total));f.write(struct.pack('<I4s',len(js),b'JSON'));f.write(js);f.write(struct.pack('<I4s',len(blob),b'BIN\0'));f.write(blob)

