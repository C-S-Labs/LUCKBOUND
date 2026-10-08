"""Assemble accepted sources read-only with Batch2 and probe actual ChunkCore."""
import json
import sys
from pathlib import Path
import bpy
import argparse
import ast

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'batch1'))
import batch1_shared as sh
import assemble_batch1 as assembly
OUT=Path('E:/BlenderAIProjects/Runtime/Emberfall_Batch2')
ROOT=HERE.parents[4]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    sh.init();sources,meta=assembly.load_sources()
    rows=json.loads((OUT/('batch2_sources.json' if args.final else 'gate_a_sources.json')).read_text())
    variants=json.loads((OUT/'batch2_variants.json').read_text()) if args.final else []
    with bpy.data.libraries.load(str(OUT/('BurnedPlainsBatch2.blend' if args.final else 'BurnedPlainsBatch2_GateA.blend')),link=False) as (a,b):b.scenes=[r['id'] for r in rows+variants]
    for row,scene in zip(rows+variants,b.scenes):sources[row['id']]=scene;meta[row['id']]=row
    if args.final:
        final_review(sources,meta)
        return
    # Use unchanged actual core: each source rebasing appears in its real sockets.
    defs={k:dict(Id=k,Role='PATH',SizeX=256,SizeZ=256,Sockets=v['sockets']) for k,v in meta.items()}
    order=['EF_ENTRY_WINDWARD_MEADOW','EF_QUIET_HOLLOW_BEND','EF_OPEN_FIELD_CLEARING','EF_LOW_SHOULDER_CLIMB','EF_RAISED_PASTURE_BEND','EF_FENCELINE_RISE','EF_WAYMARK_TERRACE','EF_SWITCHBACK_BANK','EF_DRAINAGE_CROSSING']
    source=(ROOT/'src/shared/Util/ChunkCore.luau').read_text().replace('local WeightedRandom = require(script.Parent.WeightedRandom)','local WeightedRandom = {}')
    def lua(v):
        if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+lua(x) for k,x in v.items())+'}'
        if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
        return json.dumps(v)
    code='local Core=(function()\n'+source+'\nend)()\nlocal defs='+lua(defs)+'\nlocal order='+lua(order)+'''
local results={}
for _,yaw in {0,90,180,270} do
 local placed={{ChunkId=order[1],X=0,Y=0,Z=0,Yaw=yaw,Index=1}}
 local arrived=nil;local exits={}
 for i=2,#order do
  local departure=defs[order[i-1]].Sockets[2]
  if arrived and departure.Id==arrived.Id then departure=defs[order[i-1]].Sockets[1] end
  local p,a=Core.placeAgainst(defs[order[i]],Core.worldSocket(placed[i-1],defs[order[i-1]],departure),i)
  assert(p,"profile mismatch")
  for j,q in placed do assert(not Core.overlaps(q,defs[order[j]],p,defs[order[i]]),"overlap") end
  table.insert(exits,departure.Id);table.insert(placed,p);arrived=a
 end
 local rows={}
 for i,p in placed do table.insert(rows,string.format('{"id":"%s","x":%.9f,"y":%.9f,"z":%.9f,"yaw":%d,"exit":"%s"}',order[i],p.X,p.Y,p.Z,p.Yaw,exits[i] or "END")) end
 table.insert(results,'['..table.concat(rows,",")..']')
end
print('['..table.concat(results,",")..']')
'''
    import subprocess
    target=OUT/'gate_a_layouts.luau';target.write_text(code)
    p=subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe',str(target)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr+p.stdout
    layouts=json.loads(p.stdout);(OUT/'gate_a_layouts.json').write_text(json.dumps(layouts,indent=2))
    assembly.OUT=OUT;assembly.ROOT=ROOT
    assembly.assemble('GateA1',layouts[0],sources,meta)
    # Four rotations retain the same source/mesh/profile frames; sampled assembly
    # joins are evaluated independently at each rotation without extra renders.
    checks=[]
    from mathutils import Vector
    for route in layouts:
        error=0
        for a,b in zip(route,route[1:]):
            ma=assembly.transform(a);mb=assembly.transform(b);inv=mb.inverted()
            ta=next(o for o in sources[a['id']].objects if o.name.startswith('Terrain_'))
            tb=next(o for o in sources[b['id']].objects if o.name.startswith('Terrain_'))
            va=[tuple(v.co) for v in ta.data.vertices[:4225]];vb=[tuple(v.co) for v in tb.data.vertices[:4225]]
            for t in range(-128,129,2):
                x,y={'S':(t,-128),'N':(t,128),'W':(-128,t),'E':(128,t)}[a['exit']]
                w=ma@Vector((x,y,sh.ec.surface(va,4,x,y)));local=inv@w
                error=max(error,abs(sh.ec.surface(vb,4,local.x,local.y)-local.z))
        assert error<.01
        checks.append(dict(initial_yaw=route[0]['yaw'],max_seam=error))
    payload=[]
    for r in rows:
        scene=sources[r['id']]
        for o in scene.objects:
            if not o.get('CollisionFidelity'):continue
            o.data.calc_loop_triangles()
            payload.append(dict(chunk=r['id'],name=o.name,fidelity=o['CollisionFidelity'],vertices=[[v.co.x,v.co.z,-v.co.y] for v in o.data.vertices],faces=[list(t.vertices) for t in o.data.loop_triangles]))
    (OUT/'gate_a_collision_payload.json').write_text(json.dumps(payload,separators=(',',':')))
    report=dict(kit=meta,layouts=assembly.REPORT['layouts'],rotations=checks)
    (OUT/'gate_a_review.json').write_text(json.dumps(report,indent=2))
    (HERE/'gate_a_review.json').write_text(json.dumps(dict(rotations=checks,layouts=assembly.REPORT['layouts']),indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsBatch2_Review.blend'))
    print('GATE_A_ASSEMBLY_PASS',json.dumps(checks))


def final_review(sources,meta):
    """Approved repeated-source recipes with real rebased source sockets."""
    aliases=dict(zip(['Windward','Drainage','Orchard','Ridge','Switchback','Waymark','Clearing','Wagon','Fenceline'],json.loads((HERE/'source_readback.json').read_text())))
    names={k:v['id'] for k,v in aliases.items()}
    names.update(QuietBend='EF_QUIET_HOLLOW_BEND',PastureBend='EF_RAISED_PASTURE_BEND',Shoulder='EF_LOW_SHOULDER_CLIMB',Swale='EF_SWALE_DRIFT',Saddle='EF_PASTURE_SADDLE',Ditch='EF_LONG_DITCH_VERGE',Grove='EF_LEEWARD_GROVE',Fieldstead='EF_ABANDONED_FIELDSTEAD')
    tree=ast.parse((HERE/'layout_audit.py').read_text())
    recipes=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RECIPES' for t in n.targets))
    orders={k:[names[n] for n in v] for k,v in recipes.items() if not k.startswith('Batch 1')}
    # The long route deliberately reuses eight sources, three at the repeat cap.
    defs={k:dict(Id=k,Role='PATH',SizeX=256,SizeZ=256,Sockets=v['sockets']) for k,v in meta.items()}
    def lua(v):
        if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+lua(x) for k,x in v.items())+'}'
        if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
        return json.dumps(v)
    core=(ROOT/'src/shared/Util/ChunkCore.luau').read_text().replace('local WeightedRandom = require(script.Parent.WeightedRandom)','local WeightedRandom = {}')
    code='local Core=(function()\n'+core+'\nend)()\nlocal defs='+lua(defs)+'\nlocal orders='+lua(orders)+'''
local labels={};for label in orders do table.insert(labels,label) end;table.sort(labels)
for _,label in labels do
 local order=orders[label];local placed={{ChunkId=order[1],X=0,Y=0,Z=0,Yaw=0,Index=1}};local arrived=nil;local exits={}
 for i=2,#order do
  local departure=defs[order[i-1]].Sockets[2]
  if arrived and departure.Id==arrived.Id then departure=defs[order[i-1]].Sockets[1] end
  local p,a=Core.placeAgainst(defs[order[i]],Core.worldSocket(placed[i-1],defs[order[i-1]],departure),i);assert(p,label..": socket mismatch")
  for j,q in placed do assert(not Core.overlaps(q,defs[order[j]],p,defs[order[i]]),label..": overlap") end
  table.insert(exits,departure.Id);table.insert(placed,p);arrived=a
 end
 local rows={}
 for i,p in placed do table.insert(rows,string.format('{"id":"%s","x":%.9f,"y":%.9f,"z":%.9f,"yaw":%d,"exit":"%s"}',order[i],p.X,p.Y,p.Z,p.Yaw,exits[i] or "END")) end
 print(label.."|["..table.concat(rows,",").."]")
end
'''
    import subprocess
    target=OUT/'combined_layouts.luau';target.write_text(code)
    p=subprocess.run(['C:/Users/jhpel/.rokit/bin/luau.exe',str(target)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr+p.stdout
    layouts={k:json.loads(v) for k,v in (line.split('|',1) for line in p.stdout.splitlines())}
    assembly.OUT=OUT;assembly.ROOT=ROOT
    for index,(label,route) in enumerate(layouts.items(),1):
        occurrences={}
        for row in route:
            ident=row['id'];occurrences[ident]=occurrences.get(ident,0)+1
            if occurrences[ident]%2==0 and ident+'_DRESSING_B' in meta:
                row['source_id']=ident;row['id']=ident+'_DRESSING_B'
        scene=assembly.assemble('Combined'+str(index),route,sources,meta)
        scene['RecipeLabel']=label
    report=dict(kit=meta,layouts=assembly.REPORT['layouts'],canonical_sources=17,dressing_alternatives=4)
    (OUT/'batch2_report.json').write_text(json.dumps(report,indent=2))
    (HERE/'combined_review.json').write_text(json.dumps(dict(layouts=assembly.REPORT['layouts'],canonical_sources=17,dressing_alternatives=4),indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'BurnedPlainsCombinedReview.blend'))
    print('COMBINED_LIBRARY_PASS',json.dumps({k:dict(placements=len(v['rows']),max_seam=v['max_seam'],balance=v['balance_percent']) for k,v in assembly.REPORT['layouts'].items()}))


if __name__=='__main__':main()
