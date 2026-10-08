import sys,json,math,bpy
from mathutils import Matrix,Vector
from pathlib import Path
sys.path.insert(0,'E:/BlenderAIProjects/Runtime/Emberfall_Batch1')
import batch1_shared as s
import assemble_batch1 as a
OUT=s.OUT
bpy.ops.wm.open_mainfile(filepath=str(OUT/'BurnedPlainsBatch1.blend'))
report=json.loads((OUT/'batch1_report.json').read_text())
dest=OUT/'individual';dest.mkdir(exist_ok=True)
# Road presentation for source review is explicitly outside authored source data.
for ident,meta in report['kit'].items():
    scene=bpy.data.scenes[ident];bpy.context.window.scene=scene
    terrain=next(o for o in scene.objects if o.name.startswith('Terrain_'))
    arrays=[tuple(v.co) for v in list(terrain.data.vertices)[:4225]]
    points=[]
    for x,y,z in meta['guide']:
        d=points[-1][3]+math.hypot(x-points[-1][0],y-points[-1][1]) if points else 0;points.append((x,y,z,d))
    for o in scene.objects:
        if o.get('ReviewOnly'):o.hide_render=True
    a.road(scene,points,None,lambda x,y:s.ec.surface(arrays,4,x,y),[(dict(y=0),Matrix.Identity(4),Matrix.Identity(4),arrays)])
    s.render(scene,dest/(ident+'_overview.png'))
    x,y,z,d=points[12];t=points[30];s.render(scene,dest/(ident+'_eye.png'),(x,y,z+5),t[:3])
scene=bpy.data.scenes.new('Collision_Contract_Review');bpy.context.window.scene=scene;s.light_scene(scene)
c=s.collection('TwoFrozenCollisionSources',scene)
mat=s.bp.material('edge_collision_review',(.07,.34,.43));mat.use_nodes=True
n=mat.node_tree.nodes.new('ShaderNodeWireframe');n.use_pixel_size=True;n.inputs['Size'].default_value=.8
mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.07,.34,.43,1);mix.inputs[2].default_value=(.008,.012,.014,1)
mat.node_tree.links.new(n.outputs[0],mix.inputs[0]);mat.node_tree.links.new(mix.outputs[0],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
for ident,pose in [('EF_SWITCHBACK_BANK',Matrix.Identity(4)),('EF_WAYMARK_TERRACE',Matrix.Translation((256,0,8.77636509161))@Matrix.Rotation(-math.pi/2,4,'Z'))]:
    source=bpy.data.scenes[ident]
    for original in source.objects:
        if original.type!='MESH' or not original.get('CollisionFidelity'):continue
        o=original.copy();o.data=original.data.copy();c.objects.link(o);o.matrix_world=pose@original.matrix_basis;o.hide_render=False;o.hide_viewport=False
        o.data.materials.clear();o.data.materials.append(mat)
        for p in o.data.polygons:p.material_index=0
s.render(scene,OUT/'collision_overview.png',(430,-370,340),(128,0,0))
s.render(scene,OUT/'Layout1'/'collision_seam.png',(163,-62,61),(128,0,6),145)
print('Review-only evidence refreshed; source blends and frozen geometry unchanged')
