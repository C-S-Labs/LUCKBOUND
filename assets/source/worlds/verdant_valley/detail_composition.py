"""Authored, restrained additions for the remaining Verdant Valley chunks.

Execute main(names) in the current live authoring scene. Existing objects are
never edited. Four completed reference chunks and two already-composed chunks
are excluded. Placements use terrain material, slope, footprint support and
socket-lane checks; collision collections are never used or modified.
"""
import bpy
import sys
import math
import random
import json
import hashlib
import struct
import ast
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scatter_sparse_chunks import MeshBuilder
# The legacy exporter executes on import. Extract only its literal data table.
_tree = ast.parse((HERE / 'export_verdant_valley_kit.py').read_text(encoding='utf-8'))
_expected = next(n.value for n in _tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'EXPECTED' for t in n.targets))
EXPECTED = eval(compile(ast.Expression(_expected), '<socket table>', 'eval'),
                {'__builtins__': {}, 'dict': dict, 'P': lambda *args:set(args)})

TAG = '__composition_'
REFERENCES = {'chunk_side_treasure_hollow', 'chunk_longgrass_meadow',
              'chunk_deep_clearing', 'chunk_side_wardens_clearing'}
# Each patch is a deliberately selected shoulder/landmark, not a scatter zone.
# (x, y, vegetation character, count). Shape and prop mix vary per patch.
PLANS = {
 'chunk_ancient_oak': ([(-66,30,'shade',7),(78,-40,'shade',6)], (72,-50,'acorn_bough'), 'Bare west mid-shoulder and unsupported oak base', 'Fallen forked oak bough'),
 'chunk_blossom_terrace': ([(24,67,'flower',9),(-17,-69,'flower',7)], (20,70,'petal_stones'), 'Empty upper terrace and isolated lower tree group', 'Pale stones half enclosed by blossoms'),
 'chunk_boss_sanctuary': ([(-126,39,'shade',5),(119,-47,'shade',6)], (-117,-52,'offering'), 'Repeated perimeter rocks without lower growth', 'Small weathered offering bowl beside perimeter stone'),
 'chunk_cliff_overlook_gate': ([(-65,-5,'dry',7),(66,-9,'dry',6)], (-70,-5,'cairn'), 'Two bare middle shoulders between corner groups', 'Low uneven three-stone cairn'),
 'chunk_crystal_spring_gate': ([(-29,-66,'flower',8),(56,-68,'shade',6)], (-30,-64,'crystal_shard'), 'Lower bank detached from spring composition', 'One weathered blue shard in grass'),
 'chunk_cutbank_ford': ([(-66,-23,'shade',8),(67,-61,'dry',6)], (-69,-25,'bridge_offcut'), 'Bare southern approach shoulders below the river', 'Two discarded bridge timbers'),
 'chunk_entry_dawn_meadow': ([(-69,45,'flower',8),(71,-31,'flower',6)], (-73,44,'meadow_stool'), 'Upper-left shoulder and repeated isolated grass cones', 'Small abandoned wooden meadow stool'),
 'chunk_entry_woodland_refuge': ([(-65,25,'shade',7),(67,-61,'shade',6)], (68,-62,'woodpile'), 'Unconnected west tree base and lower-right grove', 'Three uneven cut logs tucked into grove'),
 'chunk_fern_hollow': ([(70,-26,'shade',10),(-59,67,'shade',5)], (66,-29,'fern_fan'), 'Bare right middle shoulder opposite dense grove', 'Large asymmetric fern fan against rock'),
 'chunk_forgotten_orchard_gate': ([(-52,58,'flower',7),(63,-47,'shade',7)], (-53,59,'fence'), 'Upper-left orchard shoulder and unsupported southeast trees', 'Short collapsed orchard fence'),
 'chunk_high_ledge_gate': ([(-34,-68,'dry',7),(26,70,'dry',7)], (29,73,'wind_branch'), 'Bare ledge tops away from east-west route', 'Wind-stripped branch beside two stones'),
 'chunk_mossbound_ruins': ([(-15,-73,'shade',9),(45,64,'shade',6)], (-18,-73,'ruin_fragment'), 'Blank lower ruin terrace and isolated northeast grove', 'Small mossy collapsed wall fragment'),
 'chunk_mushroom_glen': ([(-65,-13,'shade',5),(61,64,'shade',5)], (-65,-13,'fungal_log'), 'Middle-west shoulder and bare northeast tree base', 'Small lilac fungi growing along fallen log'),
 'chunk_overgrown_causeway_gate': ([(-66,2,'shade',8),(71,8,'shade',6)], (-70,4,'root_bridge'), 'Bare central shoulders between repeating corner ruins', 'Exposed angular roots over a small stone'),
 'chunk_path_crossroads_copse': ([(61,57,'flower',8),(-63,-62,'shade',6)], (61,59,'young_growth'), 'Northeast copse has a lone tree with no secondary growth', 'Two leaning young shoots beside older tree'),
 'chunk_path_narrow_pass': ([(73,3,'dry',7),(-80,15,'shade',5)], (81,4,'stone_split'), 'Wide bare east recess between boulder groups', 'Split stone with growth in its gap'),
 'chunk_path_split_meadow': ([(67,67,'flower',10),(-62,-66,'flower',7)], (68,70,'swept_log'), 'Bare northeast shoulder and unsupported southwest trees', 'Partly grass-covered log with one lifted end'),
 'chunk_path_sunwash_fork': ([(-65,-24,'flower',8),(69,68,'dry',6)], (-67,-16,'golden_seedheads'), 'Empty west middle shoulder and thin northeast cluster', 'Three tall golden seedheads in a sunny grass pocket'),
 'chunk_rock_garden': ([(71,21,'dry',10),(-68,18,'shade',5)], (72,23,'stone_stack'), 'Blank east recess and repetition of isolated rock piles', 'Two broad leaning stone slabs'),
 'chunk_shaded_grove': ([(17,70,'shade',9),(-23,-72,'shade',7)], (17,72,'nurse_log'), 'Open upper/lower shoulders disconnected from tree canopies', 'New shoots growing beside a decaying log'),
 'chunk_side_forgotten_trial': ([(-74,59,'shade',6),(73,39,'dry',5)], (-78,42,'broken_plinth'), 'Bare outer approach shelves around established trial ruins', 'Half-buried broken stone plinth'),
 'chunk_stone_sentinels': ([(65,57,'dry',7),(-68,-2,'shade',6)], (65,59,'lichen_stone'), 'Empty northeast shelf and weak west mid-shoulder', 'Pale lichen on a small fallen standing-stone chip'),
 'chunk_wetland_pools': ([(38,-68,'shade',8),(-17,73,'shade',5)], (38,-71,'reed_bank'), 'Dry southeast bank and empty gap above the small pool', 'Uneven short reed bank beside a mossy rock'),
 'chunk_windward_ridge_gate': ([(-26,-72,'dry',7),(18,66,'dry',6)], (-28,-73,'weathered_stake'), 'Bare southwest ridge shoulder and unsupported north stones', 'Leaning weathered survey stake'),
}
UNCHANGED = {'chunk_path_cliff_passage': 'Dense cliff shoulders already intentionally composed; preserve open corridor.',
             'chunk_cap_cave_mouth': 'Cave and rock banks already supply hierarchy; preserve quiet approach.'}


def digest_existing(names):
    h = hashlib.sha256()
    for name in sorted(names):
        o = bpy.data.objects[name]
        h.update(name.encode())
        h.update(str(sorted(c.name for c in o.users_collection)).encode())
        for row in o.matrix_world:
            h.update(struct.pack('4d', *row))
        if o.type == 'MESH':
            for v in o.data.vertices:
                h.update(struct.pack('3f', *v.co))
            for p in o.data.polygons:
                h.update(str((tuple(p.vertices), p.material_index, p.use_smooth)).encode())
            h.update(str([m.name if m else None for m in o.data.materials]).encode())
    return h.hexdigest()


class Dressing:
    def __init__(self, name, seed):
        self.name = name
        self.chunk = bpy.data.objects[name]
        self.bvh = BVHTree.FromObject(self.chunk, bpy.context.evaluated_depsgraph_get())
        self.rng = random.Random(seed)
        self.made = []
        self.sockets = next(row[2] for row in EXPECTED.values() if row[0] == name)
        self.templates = bpy.data.collections['Temp'].objects

    def support(self, x, y, radius=3):
        # Leave 35 studs around central routes and all actual socket arms.
        for face in self.sockets:
            if face in ('N','S') and abs(x) < 35 + radius and (y >= 0 if face == 'N' else y <= 0):
                return None
            if face in ('E','W') and abs(y) < 35 + radius and (x >= 0 if face == 'E' else x <= 0):
                return None
        if self.name.startswith('chunk_entry') and abs(x) < 45 + radius:
            return None
        if self.name == 'chunk_side_forgotten_trial' and (abs(x) < 64 or y < 15):
            return None
        if self.name == 'chunk_boss_sanctuary' and abs(x) < 103:
            return None
        limit = 176 if 'boss_' in self.name else 112
        if abs(x) + radius > limit or abs(y) + radius > 112:
            return None
        center = None
        heights = []
        for dx,dy in [(0,0),(-radius-5,0),(radius+5,0),(0,-radius-5),(0,radius+5)]:
            hit,normal,index,_ = self.bvh.ray_cast(Vector((x+dx,y+dy,160)),Vector((0,0,-1)),320)
            if hit is None or normal.z < .78:
                return None
            poly = self.chunk.data.polygons[index]
            mat = self.chunk.data.materials[poly.material_index]
            if not mat or not any(k in mat.name for k in ('Grass','Earth','Moss')):
                return None
            heights.append(hit.z)
            if dx == 0 and dy == 0:
                center = hit
        if max(heights)-min(heights)>2.5:
            return None
        return center

    def link(self, obj, label, hit, solid=False, angle=0):
        obj.name = f'{self.name}{TAG}{len(self.made)+1:03d}_{label}'
        c = bpy.data.collections['VV_PROPS_SOLID' if solid else 'VV_PROPS_NONSOLID']
        if obj.name not in c.objects:
            c.objects.link(obj)
        obj.location = self.chunk.location + hit
        obj.rotation_euler = (0,0,angle)
        obj['composition_chunk'] = self.name
        obj['composition_source'] = label
        obj['collision_export'] = False
        self.made.append(obj)
        return obj

    def prop(self, kind, x, y, scale=1, angle=None, stretch=None):
        source = self.templates[kind]
        factors = Vector(stretch or (1,1,1)) * scale
        dims = Vector((source.dimensions[i]*factors[i] for i in range(3)))
        radius = max(dims.x,dims.y)/2
        hit = self.support(x,y,radius)
        if hit is None:
            return None
        obj=source.copy()
        obj.data=source.data.copy()
        obj.scale=Vector((source.scale[i]*factors[i] for i in range(3)))
        obj.hide_render=False
        obj.hide_viewport=False
        angle=self.rng.uniform(-math.pi,math.pi) if angle is None else angle
        self.link(obj,kind,hit,kind in ('rock','log'),angle)
        obj.location.z -= min(v.co.z*obj.scale.z for v in obj.data.vertices)+.12
        return obj

    def patch(self,x,y,character,count):
        # Different hand-chosen species balances and irregular, compact footprints.
        mix={'shade':['Star_bush','Star_bush','grass_tuft','flowering_bush'],
             'flower':['flowering_bush','flowering_bush','Star_bush','grass_tuft'],
             'dry':['rock','grass_tuft','grass_tuft','Star_bush']}[character]
        placed=[]
        for attempt in range(100):
            dx=self.rng.uniform(-13,13)
            dy=self.rng.uniform(-10,10)
            if dx*dx/169+dy*dy/100>1 or any((dx-a)**2+(dy-b)**2<4.5**2 for a,b in placed):
                continue
            kind=self.rng.choice(mix)
            size=self.rng.uniform(1.05,1.6) if kind!='rock' else self.rng.uniform(.4,.72)
            if self.prop(kind,x+dx,y+dy,size):
                placed.append((dx,dy))
            if len(placed)>=count:
                break
        return len(placed)

    def mesh(self,builder,label,x,y,materials,solid=True,radius=7,angle=0):
        hit=self.support(x,y,radius)
        if hit is None:
            return None
        coll=bpy.data.collections['VV_PROPS_SOLID' if solid else 'VV_PROPS_NONSOLID']
        obj=builder.finish('CompositionPending',coll,[bpy.data.materials[m] for m in materials])
        return self.link(obj,label,hit,solid,angle)

    def feature(self,x,y,kind):
        b=MeshBuilder()
        wood=['VV_Bark','VV_WaymarkerWood','VV_Leaf']
        stone=['VV_Rock','VV_RockLight','VV_DetailMoss']
        if kind in ('acorn_bough','wind_branch','root_bridge'):
            # Restrained angular taper, readable fork, no tiny twigs.
            b.beam((-6,0,.6),(3,1,.7),1.1,0)
            b.beam((2,1,.7),(7,4,1.1),.7,0)
            b.beam((1,1,.7),(5,-3,.5),.55,0)
            if kind=='wind_branch':
                b.vertices=[(vx,vy*.38,vz*.7) for vx,vy,vz in b.vertices]
            if kind=='root_bridge':
                b.beam((-6,0,.6),(-8,-3,0),.5,0)
                self.prop('rock',x+1,y+1,.52)
            return self.mesh(b,kind,x,y,wood,radius=9,angle=.35)
        if kind=='meadow_stool':
            b.box((0,0,2.7),(4.6,3,1),0)
            for dx,dy in [(-1.7,-.9),(1.7,-.9),(-1.7,.9),(1.7,.9)]:
                b.beam((dx,dy,0),(dx,dy,2.4),.6,1)
            return self.mesh(b,'meadow_stool',x,y,['VV_WaymarkerWood','VV_Bark'],radius=4,angle=-.35)
        if kind=='golden_seedheads':
            for dx,dy,h in [(-3,0,4.8),(0,1,3.9),(3,-1,3.1)]:
                b.beam((dx,dy,0),(dx+.3,dy,h),.18,0)
                b.frustum((dx+.3,dy,h),.8,.5,.35,1,sides=6)
                for ox,oy in [(-.9,0),(.8,.4),(0,-.8)]:
                    b.frustum((dx+.3+ox,dy+oy,h-.15),.6,.42,.25,2,sides=5)
            return self.mesh(b,'golden_seedheads',x,y,['VV_FlowerStem','VV_FlowerHeart','VV_FlowerCream'],False,radius=6)
        if kind=='petal_stones':
            self.prop('rock',x,y,.75,stretch=(1.2,.9,.35))
            for dx,dy,s in [(-4,1,1.6),(2,4,1.15),(5,-1,.9)]:
                self.prop('flowering_bush',x+dx,y+dy,s)
            return self.made[-1] if self.made else None
        if kind=='offering':
            # Low, open eight-sided bowl, not a new major shrine.
            verts=[]
            for radius,z in [(2.5,0),(3.1,1.5),(2.3,1.5),(1.7,.5)]:
                verts.extend((radius*math.cos(i*math.tau/8),radius*math.sin(i*math.tau/8),z) for i in range(8))
            faces=[]
            for ring in range(3):
                faces.extend((ring*8+i,ring*8+(i+1)%8,(ring+1)*8+(i+1)%8,(ring+1)*8+i) for i in range(8))
            faces.append(tuple(range(24,32)))
            b.add(verts,faces,0)
            return self.mesh(b,kind,x,y,stone,radius=4)
        if kind=='cairn':
            base=self.prop('rock',x,y,.68,stretch=(1.1,1,.55))
            if not base:return None
            top=base.location.z+max(v.co.z*base.scale.z for v in base.data.vertices)
            for size,shift in [(.42,(.4,.2)),(.25,(-.1,.5))]:
                o=self.prop('rock',x+shift[0],y+shift[1],size,stretch=(1,1,.55))
                if o:
                    o.location.z=top-min(v.co.z*o.scale.z for v in o.data.vertices)-.08
                    top=o.location.z+max(v.co.z*o.scale.z for v in o.data.vertices)
            return base
        if kind=='crystal_shard':
            b.add([(-1.3,-.9,0),(1.2,-.7,0),(.9,1,0),(-1,1,0),(.3,.2,4)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],0)
            return self.mesh(b,kind,x,y,['VV_CrystalBlue'],radius=3)
        if kind=='bridge_offcut':
            b.box((0,0,.45),(11,1.4,.9),0)
            b.beam((-3,-2,.3),(5,-3,.7),.85,1)
            return self.mesh(b,kind,x,y,['VVBridge_WarmWood','VVBridge_CutWood'],radius=7,angle=-.45)
        if kind=='woodpile':
            a=self.prop('log',x,y,.72,angle=.2)
            self.prop('log',x+1,y+3,.63,angle=.08)
            c=self.prop('log',x,y+1.5,.59,angle=.14)
            if a and c:c.location.z+=1.3
            return a
        if kind=='fern_fan':
            self.prop('rock',x+4,y,.64)
            for dx,dy,size,rot in [(0,0,2.0,.3),(-4,1,1.4,1.2),(1,-4,1.15,-.8)]:
                self.prop('Star_bush',x+dx,y+dy,size,angle=rot,stretch=(1.1,1,1.6))
            return self.made[-1]
        if kind=='fence':
            b.beam((-5,0,0),(-5,.3,5),.9,0)
            b.beam((4,1,0),(5,1,3.2),.9,0)
            b.beam((-5,0,3.5),(5,1,2.2),.7,1)
            b.beam((-4,0,.4),(3,-2,.2),.65,1)
            return self.mesh(b,kind,x,y,wood,radius=8,angle=.28)
        if kind in ('ruin_fragment','broken_plinth','stone_stack','lichen_stone','stone_split'):
            if kind=='ruin_fragment':
                b.box((-3,0,1),(5,2.6,2),0);b.box((2,.4,.7),(4,2.4,1.4),1);b.box((-3,.1,2.7),(4,2.5,1.4),0)
                b.foliage((-4,-1,1.9),(1.8,1,.4),2)
            elif kind=='broken_plinth':
                b.box((0,0,.6),(5.6,4.6,1.2),0)
                b.add([(-1.8,-1.1,1.2),(.7,-1.1,1.2),(.7,1.5,1.2),(-1.8,1.5,1.2),
                       (-1.8,-1.1,3.8),(.7,-1.1,2.7),(.7,1.5,1.9),(-1.8,1.5,3.3)],
                      [(0,3,2,1),(4,5,6),(4,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],1)
                b.foliage((3.2,1.6,.35),(1.1,.7,.45),1)
            elif kind=='stone_stack':
                b.beam((-4,0,.4),(1,1,3),2,0);b.beam((4,1,.5),(1.5,1.5,3.5),1.6,1)
            elif kind=='lichen_stone':
                b.beam((-3,0,.5),(3,.5,1.6),2,0)
                b.foliage((0,-.8,1.1),(1.6,.65,.45),1)
            else:
                self.prop('rock',x-2.5,y,.64,stretch=(.7,1,1.2))
                self.prop('rock',x+2.7,y+1,.5,stretch=(.7,1,1))
                return self.prop('Star_bush',x,y,.85)
            return self.mesh(b,kind,x,y,stone,radius=7,angle=-.3)
        if kind=='fungal_log':
            a=self.prop('log',x,y,1.1,angle=.4)
            for dx,dy,h in [(-3,-1,1.9),(1,0,1.3),(4,2,.9)]:
                b.frustum((dx,dy,1),.22,.17,h,0,sides=6)
                b.frustum((dx,dy,1+h),.85*h,.2*h,.4*h,1,sides=7)
            self.mesh(b,'log_fungi',x,y,['VVFix_MushroomStemIvory','VVFix_MushroomCapLilac'],False,radius=6,angle=.4)
            return a
        if kind in ('young_growth','nurse_log'):
            if kind=='nurse_log':self.prop('log',x-3,y,1.05,angle=-.7)
            for dx,dy,h in [(0,0,5),(4,2,3.6)]:
                b.beam((dx,dy,0),(dx+.6,dy,h),.4,0)
                b.foliage((dx+.5,dy,h),(1.8,1.4,2),2)
            return self.mesh(b,kind,x,y,wood,False,radius=7)
        if kind=='swept_log':
            a=self.prop('log',x,y,1.2,angle=.6)
            if a:
                # Mesh edit applies only to this independent copy.
                for v in a.data.vertices:v.co.z+=.07*v.co.x
            self.prop('grass_tuft',x-4,y-2,1.6)
            return a
        if kind=='reed_bank':
            self.prop('rock',x+4,y,.55)
            for dx,dy,h in [(-3,0,5),(0,1,4),(2,-2,3.4),(-1,-2,2.8)]:
                b.beam((dx,dy,0),(dx+.35,dy,h),.22,0)
                b.frustum((dx+.35,dy,h-.8),.36,.3,.9,1,sides=5)
            return self.mesh(b,kind,x,y,['VV_Leaf','VV_Earth'],False,radius=6)
        if kind=='weathered_stake':
            b.beam((0,0,0),(.7,.4,5.8),.8,0)
            b.box((.6,.4,4.6),(1.1,1,1),1)
            return self.mesh(b,kind,x,y,['VV_WaymarkerWood','VV_RockLight'],radius=3,angle=.4)
        raise ValueError(kind)


def main(names=None):
    names=list(names or PLANS)
    assert not REFERENCES.intersection(names)
    assert all(name in PLANS for name in names)
    assert 'Extra_Details_Backup' in bpy.data.filepath
    original=set(bpy.data.objects.keys())
    before=digest_existing(original)
    report={}
    for name in names:
        assert not any(o.name.startswith(name+TAG) for o in bpy.data.objects), 'Already composed: '+name
        patches,feature,reason,detail=PLANS[name]
        d=Dressing(name,3000+list(PLANS).index(name))
        unique=d.feature(*feature)
        if not unique:
            raise RuntimeError('Feature location requires review: '+name)
        patch_counts=[d.patch(*p) for p in patches]
        report[name]={'issue':reason,'changes':'Two restrained shoulder/landmark clusters using Temp props',
                      'unique_detail':detail,'added':len(d.made),'patch_counts':patch_counts,
                      'objects':[o.name for o in d.made]}
    bpy.context.view_layer.update()
    assert before==digest_existing(original), 'Existing scene content changed'
    record=Path('E:/BlenderAIProjects/Projects/Composition_Record.json')
    old=json.loads(record.read_text()) if record.exists() else {}
    old.update(report)
    old['_unchanged']=UNCHANGED
    old['_protected_existing_digest']=before
    record.write_text(json.dumps(old,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps({n:{k:v for k,v in row.items() if k!='objects'} for n,row in report.items()}))


def refine_review():
    """Apply the recorded visual-review corrections to this pass's objects only."""
    assert not bpy.context.scene.get('vv_composition_reviewed'), 'Visual refinements already applied'
    original={o.name for o in bpy.data.objects if TAG not in o.name}
    before=digest_existing(original)
    for name in ('chunk_entry_dawn_meadow','chunk_path_sunwash_fork'):
        old=[o for o in bpy.data.objects if o.name.startswith(name+TAG)
             and int(o.name.split(TAG)[1].split('_')[0])<=4]
        for o in old:
            bpy.data.objects.remove(o,do_unlink=True)
        d=Dressing(name,1)
        assert d.feature(*PLANS[name][1])
    # Thin the densest planting around Blossom and the orchard fence. Keep
    # asymmetry and a few strays; expose the focal object rather than hide it.
    for name,count in [('chunk_blossom_terrace',3),('chunk_forgotten_orchard_gate',2),
                       ('chunk_fern_hollow',2),('chunk_mossbound_ruins',2)]:
        x,y,_=PLANS[name][1]
        nearby=[o for o in bpy.data.objects if o.name.startswith(name+TAG)
                and ('flowering_bush' in o.name or 'grass_tuft' in o.name)
                and int(o.name.split(TAG)[1].split('_')[0])>4]
        nearby.sort(key=lambda o:(o.location.x-bpy.data.objects[name].location.x-x)**2
                     +(o.location.y-bpy.data.objects[name].location.y-y)**2)
        for o in nearby[:count]:
            bpy.data.objects.remove(o,do_unlink=True)
    # A narrower wind-swept branch silhouette differentiates the exposed ledge
    # from Ancient Oak's heavier forked bough.
    o=bpy.data.objects['chunk_high_ledge_gate__composition_001_wind_branch']
    for v in o.data.vertices:
        v.co.y*=.38
        v.co.z*=.7
    d=Dressing('chunk_side_forgotten_trial',1)
    o=bpy.data.objects['chunk_side_forgotten_trial__composition_001_broken_plinth']
    o.location=d.chunk.location+d.support(-78,42,7)
    o=bpy.data.objects['chunk_stone_sentinels__composition_001_lichen_stone']
    for p in o.data.polygons:
        if p.material_index==2:p.material_index=1
    bpy.context.view_layer.update()
    assert before==digest_existing(original)
    record=Path('E:/BlenderAIProjects/Projects/Composition_Record.json')
    rows=json.loads(record.read_text())
    for name in PLANS:
        objects=[o.name for o in bpy.data.objects if o.name.startswith(name+TAG)]
        rows[name]['objects']=objects
        rows[name]['added']=len(objects)
        rows[name]['unique_detail']=PLANS[name][3]
        rows[name]['visual_review']='Overhead, route and low feature view reviewed; broad grass and socket lanes retained.'
    rows['_original_digest']=before
    bpy.context.scene['vv_composition_reviewed']=True
    record.write_text(json.dumps(rows,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print('VISUAL_REFINEMENTS_SAVED',sum(rows[n]['added'] for n in PLANS))


# Owner review: tight islands left accidental dead shoulders. These broad,
# irregular planting areas follow each chunk's own silhouette and landmarks.
# x, y, half-width, half-depth, local count (existing plants reused first).
SPREAD_AREAS = {
 'chunk_ancient_oak':[(-66,65,21,28,9),(-75,1,22,24,8),(71,48,24,33,7),(76,-63,23,27,9)],
 'chunk_blossom_terrace':[(-56,67,29,20,7),(33,78,30,22,9),(-38,-65,30,24,9),(60,-70,25,21,6)],
 'chunk_boss_sanctuary':[(-135,61,22,25,5),(-130,-24,25,30,5),(131,56,23,25,4),(132,-47,24,27,5)],
 'chunk_cliff_overlook_gate':[(-69,45,22,26,7),(-77,-9,22,32,9),(71,28,25,30,8),(69,-62,24,25,7)],
 'chunk_crystal_spring_gate':[(-54,-70,30,25,10),(39,-67,33,24,10),(-9,79,34,22,6)],
 'chunk_cutbank_ford':[(-69,-14,22,27,9),(-73,-70,21,23,9),(74,-21,24,26,7),(71,-76,24,20,8)],
 'chunk_entry_dawn_meadow':[(-76,55,20,28,9),(-78,-19,24,32,9),(76,38,24,32,8),(71,-69,22,24,8)],
 'chunk_entry_woodland_refuge':[(-78,47,22,27,8),(-70,-18,21,26,9),(74,39,24,33,9),(70,-67,23,24,8)],
 'chunk_fern_hollow':[(-72,67,23,25,7),(-77,-4,22,32,6),(72,20,24,28,9),(75,-63,23,26,8)],
 'chunk_forgotten_orchard_gate':[(-53,68,30,23,9),(51,68,29,23,9),(68,-39,25,28,8),(-69,-62,22,25,7)],
 'chunk_high_ledge_gate':[(-59,68,28,24,7),(33,76,35,22,9),(-33,-72,30,24,10),(59,-62,25,24,7)],
 'chunk_mossbound_ruins':[(-58,73,27,23,6),(34,71,32,24,9),(-44,-76,30,22,10),(59,-64,28,24,7)],
 'chunk_mushroom_glen':[(-72,37,24,24,6),(-74,-40,24,29,7),(72,62,22,25,6),(74,-65,23,23,4)],
 'chunk_overgrown_causeway_gate':[(-72,48,23,30,8),(-78,-21,23,28,9),(76,36,23,34,8),(70,-59,24,25,7)],
 'chunk_path_crossroads_copse':[(-71,66,24,23,6),(70,67,25,24,9),(-68,-67,24,24,8),(71,-67,23,23,7)],
 'chunk_path_narrow_pass':[(-81,48,18,27,6),(-80,-21,19,29,7),(79,7,22,32,10),(73,-66,23,23,6)],
 'chunk_path_split_meadow':[(-66,67,24,24,6),(68,66,26,25,11),(-64,-71,29,23,9),(71,-69,24,24,7)],
 'chunk_path_sunwash_fork':[(-73,55,23,28,6),(-71,-14,23,28,10),(68,67,25,23,8),(71,-67,25,24,7)],
 'chunk_rock_garden':[(-75,43,22,30,6),(-72,-28,24,32,7),(76,41,24,30,11),(75,-40,23,32,9)],
 'chunk_shaded_grove':[(-55,68,27,23,5),(29,74,35,23,9),(-36,-74,33,24,10),(61,-65,25,23,6)],
 'chunk_side_forgotten_trial':[(-82,56,17,31,9),(85,55,17,30,9)],
 'chunk_stone_sentinels':[(-70,56,25,28,6),(-77,-8,23,31,9),(74,60,25,25,10),(72,-47,26,27,7)],
 'chunk_wetland_pools':[(-8,76,31,20,7),(51,-67,32,24,10),(-41,-88,26,15,6),(62,67,25,24,5)],
 'chunk_windward_ridge_gate':[(-55,69,28,24,7),(31,70,31,25,8),(-38,-75,31,24,10),(58,-66,28,23,7)],
}
FEATURE_OBJECTS = dict(zip(PLANS, [1,4,1,3,1,1,1,3,4,1,1,1,2,2,1,3,2,1,1,2,1,1,2,1]))


def spread_review(names=None):
    """Loosen this pass's planting, preserving original art and unique details."""
    names=list(names or SPREAD_AREAS)
    assert not REFERENCES.intersection(names)
    assert not bpy.context.scene.get('vv_composition_spread'), 'Spread review already applied'
    protected={o.name for o in bpy.data.objects if TAG not in o.name}
    # Keep every custom feature and its supporting first props in place.
    for n in names:
        protected.update(o.name for o in bpy.data.objects if o.name.startswith(n+TAG)
                         and int(o.name.split(TAG)[1].split('_')[0])<=FEATURE_OBJECTS[n])
    before=digest_existing(protected)
    record=Path('E:/BlenderAIProjects/Projects/Composition_Record.json')
    rows=json.loads(record.read_text())
    report={}
    for n in names:
        d=Dressing(n,5100+list(PLANS).index(n))
        all_added=sorted([o for o in bpy.data.objects if o.name.startswith(n+TAG)],key=lambda o:o.name)
        movable=[o for o in all_added if o.name not in protected]
        # Start new names beyond the existing indices without replacing meshes.
        d.made=[None]*max(int(o.name.split(TAG)[1].split('_')[0]) for o in all_added)
        blockers=[]
        for o in bpy.data.collections['VV_PROPS_SOLID'].objects:
            if o.name.startswith(n+'__') and o.name not in {a.name for a in movable}:
                pts=[o.matrix_world@Vector(p)-d.chunk.location for p in o.bound_box]
                blockers.append((min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts)))
        accepted=[]
        cursor=0
        initial=len(all_added)
        area_counts=[]
        character=PLANS[n][0][0][2]
        mix={'shade':['Star_bush','grass_tuft','Star_bush','flowering_bush','rock'],
             'flower':['flowering_bush','grass_tuft','Star_bush','flowering_bush','rock'],
             'dry':['rock','grass_tuft','Star_bush','grass_tuft']}[character]
        for ax,ay,rx,ry,wanted in SPREAD_AREAS[n]:
            placed=0
            for attempt in range(360):
                # Ragged wide shoulders, with occasional pairs and separated
                # offspring. No fixed patch outline and no equal spacing.
                x=ax+d.rng.uniform(-rx,rx)
                y=ay+d.rng.uniform(-ry,ry)
                if any((x-px)**2+(y-py)**2<d.rng.uniform(7.5,11)**2 for px,py in accepted):continue
                if any(loX-2<x<hiX+2 and loY-2<y<hiY+2 for loX,hiX,loY,hiY in blockers):continue
                if cursor<len(movable):
                    o=movable[cursor]
                    source=o['composition_source']
                    radius=max(o.dimensions.x,o.dimensions.y)/2
                    hit=d.support(x,y,radius)
                    if hit is None:continue
                    o.location=d.chunk.location+hit
                    o.location.z-=min(v.co.z*o.scale.z for v in o.data.vertices)+.12
                    o.rotation_euler.z=d.rng.uniform(-math.pi,math.pi)
                    cursor+=1
                else:
                    source=d.rng.choice(mix)
                    size=d.rng.uniform(.65,1.45) if source=='rock' else d.rng.uniform(.9,1.6)
                    if not d.prop(source,x,y,size):continue
                accepted.append((x,y))
                placed+=1
                if placed>=wanted:break
            area_counts.append(placed)
        # An uncommon unresolved existing prop stays where it was rather than
        # being forced onto a slope, route or boundary.
        final=[o.name for o in bpy.data.objects if o.name.startswith(n+TAG)]
        rows[n]['objects']=final
        rows[n]['added']=len(final)
        rows[n]['distribution_review']={'moved':cursor,'new':len(final)-initial,'areas':area_counts,
            'intent':'Broad, uneven shoulder groups and linking strays; original focal detail preserved.'}
        report[n]=rows[n]['distribution_review']
    bpy.context.view_layer.update()
    assert before==digest_existing(protected), 'Original or signature art changed'
    rows['_distribution_review']='Owner found initial planting too clustered. Spread existing dressing into wider shoulders and added sparse linking growth in previously empty gaps.'
    record.write_text(json.dumps(rows,indent=2))
    bpy.context.scene['vv_composition_spread']=True
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(json.dumps(report))
