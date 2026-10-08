"""Three frozen Area I field places; assembly owns road and burn appearance."""
import json
import math
import sys
from pathlib import Path

# Sources use the stable API beside this file.
API = Path(__file__).resolve().parent
sys.path.insert(0, str(API))
import batch1_shared as shared


def gaussian(x, y, cx, cy, rx, ry):
    return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)


def clearing_land(x, y):
    # Broad shallow open saddle; unequal side hills frame the combat lawn.
    return (6.5*gaussian(x,y,-77,27,47,72)
            +4.8*gaussian(x,y,84,-17,39,64)
            -2.3*gaussian(x,y,7,11,58,65)
            -1.8*gaussian(x,y,-41,-42,24,74)
            +.55*math.sin(x/28)*math.cos(y/45))


def verge_land(x, y):
    # Uphill left bend skirts a raised inside shoulder and shallow outer swale.
    return (7.4*gaussian(x,y,-26,45,59,48)
            -3.1*gaussian(x,y,67,6,31,86)
            +3.8*gaussian(x,y,-66,-64,37,39)
            -.8*math.sin((x+y)/39))


def rise_land(x, y):
    # A broad oblique pasture ridge, with drainage running below the fence.
    return (5.5*gaussian(x,y,-64,18,52,83)
            -3.4*gaussian(x,y,51,24,24,80)
            +3.1*gaussian(x,y,89,-68,36,40)
            +.75*math.sin(y/31)*math.cos(x/51))


def state_objects(ctx, objects, x, y, kind, role):
    anchor=dict(type=kind,x=x,y=y,z=ctx.ground(x,y),override=None)
    ctx.anchors.append(anchor)
    for obj in objects:
        obj['StateAnchor']=json.dumps(anchor)
        obj['StateRole']=role
        # Source presentation is neutral stressed timber, never fixed char.
        obj.data.materials.clear()
        obj.data.materials.append(shared.bp.WOOD)


def field_tree(ctx, x, y, height):
    before=set(ctx.c.objects)
    ctx.tree(x,y,height)
    for obj in set(ctx.c.objects)-before:
        for i,mat in enumerate(obj.data.materials):
            if mat==shared.bp.LEAF[0]:obj.data.materials[i]=shared.bp.LEAF[1]


def field_fence(ctx, points):
    before=set(ctx.c.objects)
    ctx.fence(points,damaged=True)
    # Each physical component samples its own local root, rather than one
    # stage for a hundred-stud fence. Rails use their mesh-centre root.
    for obj in set(ctx.c.objects)-before:
        xs=[v.co.x for v in obj.data.vertices]
        ys=[v.co.y for v in obj.data.vertices]
        x,y=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
        state_objects(ctx,[obj],x,y,'fence','timber')


def dress_clearing(ctx):
    # Low interrupted walls contain the lawn without becoming a hero landmark.
    for x in (-76,78):
        ctx.wall([(x+3*math.sin(y/26),y) for y in range(-68,77,6)
                  if not (4<y<27 or -44<y<-24)])
    for x,y,h in [(-92,67,27),(-80,-74,24),(93,61,25),(101,-37,22)]:
        field_tree(ctx,x,y,h)
    for x,y,s in [(-69,64,2.2),(86,-52,2),(-91,-28,1.5)]:ctx.rock(x,y,s)
    ctx.refuge(-48,-38,17,31,.25,'Shallow drainage behind low western field wall')


def wagon(ctx, x, y):
    before=set(ctx.c.objects);z=ctx.ground(x,y)
    # Five-stud-wide broken farm wagon: open deck, missing side boards,
    # a dropped front corner and an attached, uneven pair of shafts.
    for dx in (-2,-1,0,1,2):
        ctx.box('wagon_deck_board',x+dx,y,z+1.65,.46,3.2,.16)
    for yy in (-2.1,2.1):
        ctx.beam('wagon_axle',(x-3.15,y+yy,z+1.15),(x+3.15,y+yy,z+1.15),.25)
    for dx in (-2.75,2.75):
        for yy in (-2.1,2.1):
            center=(x+dx,y+yy,z+1.3)
            radius=1.25 if yy>0 else 1.05
            # Polygonal wooden wheel with hub, rim and crossing spokes.
            for i in range(10):
                a=i*math.tau/10;b=(i+1)*math.tau/10
                p=(center[0],center[1]+radius*math.cos(a),center[2]+radius*math.sin(a))
                q=(center[0],center[1]+radius*math.cos(b),center[2]+radius*math.sin(b))
                ctx.beam('wagon_wheel_rim',p,q,.13)
                if i%2==0:ctx.beam('wagon_wheel_spoke',center,p,.09)
    for dx in (-2.2,2.2):
        for yy in (-2.8,2.8):
            ctx.beam('wagon_side_stake',(x+dx,y+yy,z+1.7),(x+dx+.2,y+yy,z+4),.16)
        for hh in (2.3,3.05):
            # Eastern side has a readable missing rear half.
            end=0 if dx>0 else 2.8
            ctx.beam('wagon_side_board',(x+dx,y-2.8,z+hh),(x+dx,y+end,z+hh-.15),.17)
        ctx.beam('wagon_shaft',(x+dx*.6,y-2.8,z+1.6),(x+dx*.7,y-8.2,z+.35),.19)
    ctx.beam('wagon_detached_board',(x+3,y+1,z+.2),(x+7,y+4,z+.35),.2)
    state_objects(ctx,set(ctx.c.objects)-before,x,y,'wagon','timber')


def dress_verge(ctx):
    wagon(ctx,-5,-45)
    # An old pasture edge follows the uphill inside of the turn; the other
    # side remains usable broad ground for a later assembly-derived front.
    field_fence(ctx,[(-63,28),(-53,35),(-42,40),(-29,43),(-16,47),(0,51),(13,55)])
    for x,y,h in [(88,-62,25),(102,27,29),(-39,75,24),(-96,-79,22)]:
        field_tree(ctx,x,y,h)
    for x,y,s in [(-38,53,2.4),(-29,61,1.7),(85,42,1.5)]:ctx.rock(x,y,s)
    ctx.refuge(69,4,19,48,.28,'Outer shallow swale below the ascending track')
    # Short stems are deliberate roadside stubble opportunities. Their
    # authored roots let assembly choose active/front/char appearance later.
    for k in range(38):
        yy=-82+k*2.9;xx=35+10*math.sin(k*.22)
        if k%7==0:continue
        z=ctx.ground(xx,yy)
        obj=ctx.beam('roadside_stubble', (xx,yy,z), (xx+.15,yy+.05,z+.42),.045)
        state_objects(ctx,[obj],xx,yy,'stubble','stem')


def dress_rise(ctx):
    # Fence follows the winding track at a clear offset. Three missing rail
    # bays and a drainage break avoid a continuous guard-rail appearance.
    guide=ctx.spec['guide']
    field_fence(ctx,[(guide[i][0]+19,guide[i][1]) for i in range(12,35,3)])
    field_fence(ctx,[(guide[i][0]+21,guide[i][1]) for i in range(42,56,3)])
    for x,y,h in [(-96,71,29),(-75,-48,25),(104,83,23)]:field_tree(ctx,x,y,h)
    # A distant cross-field wall provides countryside depth across the ridge.
    ctx.wall([(x,75+5*math.sin(x/22)) for x in range(-101,-34,6)])
    for x,y,s in [(65,14,1.7),(74,20,1.2),(-57,64,2.1)]:ctx.rock(x,y,s)
    ctx.refuge(52,23,15,49,.3,'Low drainage strip sheltered below pasture ridge')


def main():
    shared.init();rows=[];contexts=[]
    specs=[
        (dict(id='EF_OPEN_FIELD_CLEARING',title='Open Field Clearing',
              purpose='Quiet ordinary connective and open combat field; boundary frames empty space',
              seed=51061,edges={'S':('HOLLOW',0),'N':('HOLLOW',0)},
              land=clearing_land,guide=shared.straight(4),grass_count=2900,
              grass_filter=lambda x,y:abs(x)>42 or abs(y)>57),dress_clearing),
        (dict(id='EF_BURN_FRONT_VERGE',title='Burn Front Verge',
              purpose='Rising left bend with damaged wagon and roadside stubble opportunities; assembly assigns front',
              seed=51062,edges={'S':('HOLLOW',0),'W':('CREST',24)},
              land=verge_land,guide=shared.turn('W'),grass_count=3300,
              landmark='Broken roadside farm wagon',
              grass_filter=lambda x,y:not (25<x<51 and -80<y<27)),dress_verge),
        (dict(id='EF_FENCELINE_RISE',title='Fenceline Rise',
              purpose='Straight low +16 rise through dry pasture gaps, roadside fence and distant countryside',
              seed=51063,edges={'S':('CREST',0),'N':('CREST',16)},
              land=rise_land,guide=shared.straight(7),grass_count=2850,
              grass_filter=lambda x,y:not (23<x<49 and -17<y<36)),dress_rise),
    ]
    for spec,dress in specs:
        ctx,row=shared.build(spec,dress)
        contexts.append(ctx);rows.append(row)
    shared.finish_lane('fields',rows,contexts)


if __name__=='__main__':main()
