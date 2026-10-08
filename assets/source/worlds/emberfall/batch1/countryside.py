"""Three frozen countryside sources for approved Burned Plains Batch 1."""
import sys, math, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch1_shared as sh

def bump(x,y,cx,cy,rx,ry):
    return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)

def meadow_land(x,y):
    return (11*bump(x,y,-65,34,52,76)+5*bump(x,y,66,-47,60,50)
            -3*bump(x,y,32,45,35,68)+1.2*math.sin(y/36)*math.sin(x/55))

def drainage_land(x,y):
    channel= -5.2*math.exp(-((y+12+8*math.sin(x/64))/11)**2)
    fill=5.0*math.exp(-(x/12)**2-((y+12)/15)**2)
    return (7*bump(x,y,-70,61,60,45)+9*bump(x,y,78,-61,62,58)+channel+fill)

def orchard_land(x,y):
    return (8*bump(x,y,-62,43,65,61)+4*bump(x,y,30,77,80,51)
            -2*bump(x,y,53,-55,50,42)+.8*math.sin(x/36)*math.sin(y/43))

def timber(ctx,obj,root,role):
    anchor=dict(type='timber',x=root[0],y=root[1],override=None)
    obj['StateAnchor']=json.dumps(anchor);obj['StateRole']=role

def gate(ctx,x,y):
    root=(x,y)
    z=ctx.ground(x,y)
    for dx in (-3.6,3.6):
        timber(ctx,ctx.box('Field_gate_post',x+dx,y,z+2,.30,.32,2),root,'post')
    for h in (1,2.6):
        timber(ctx,ctx.beam('Field_gate_rail',(x-3.4,y,z+h),(x+3.4,y,z+h),.15),root,'rail')
    timber(ctx,ctx.beam('Field_gate_brace',(x-3.4,y,z+.6),(x+3.4,y,z+3),.13),root,'brace')

def fence(ctx,points,damaged=False):
    before=set(ctx.c.objects);ctx.fence(points,damaged)
    root=points[len(points)//2]
    for obj in set(ctx.c.objects)-before:timber(ctx,obj,root,'fence')

def wall(ctx,points):
    ctx.wall(points)
    # A sparse upper course gives believable dry-stone construction without
    # turning the field boundary into a high defensive wall.
    for i,(x,y) in enumerate(points):
        if i%2==0:
            ctx.box('Field_wall_cap',x,y,ctx.ground(x,y)+2.55,1.8,.77,.35,sh.bp.STONE)

def road(ctx):
    guide=ctx.spec['guide'];verts=[];faces=[]
    for i,(x,y) in enumerate(guide):
        a=guide[max(0,i-1)];b=guide[min(len(guide)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        for s in (-1,-.5,0,.5,1):
            px,py=x-s*dy/length*4.2,y+s*dx/length*4.2
            verts.append((px,py,ctx.ground(px,py)+.18))
        if i:
            for q in range(4):faces.append((5*i-5+q,5*i-4+q,5*i+1+q,5*i+q))
    obj=sh.bp.mesh('Authored_field_track',verts,faces,[],ctx.c)
    sh.colours(obj)
    for c in obj.data.color_attributes['Col'].data:c.color=(.24,.175,.095,1)
    obj['AppearanceRole']='road';obj['LocalWidth']=8.4;obj['ReviewOnly']=True

def meadow(ctx):
    road(ctx)
    # Quiet open maintained field with the wall enclosing its windward flank.
    wall(ctx,[(-42,y) for y in range(-76,65,5)])
    wall(ctx,[(x,-77) for x in range(-40,-19,5)])
    wall(ctx,[(x,-77) for x in range(18,65,5)])
    gate(ctx,-13,-77)
    fence(ctx,[(57,y) for y in (-62,-45,-28,-11,6)],False)
    ctx.refuge(-17,-28,27,53,.78,'Maintained low field sheltered behind windward dry-stone wall')
    for x,y,h in [(-69,51,33),(-85,63,24),(-71,77,27),(73,68,25),(84,48,20)]:
        ctx.tree(x,y,h,style='windbreak')
    for x,y,s in [(-48,68,2.8),(-52,63,1.7),(69,-67,2.1)]:ctx.rock(x,y,s)
    ctx.box('Stone_waymarker',13,-44,ctx.ground(13,-44)+1.8,.65,.8,1.8,sh.bp.STONE)

def drainage(ctx):
    road(ctx)
    # Low wet drainage meanders across the route; compact stone culvert mouths
    # sit outside travel clearance and explain the interruption in fire spread.
    for sign in (-1,1):
        x=sign*14.5;y=-12
        z=ctx.ground(x,y)
        for dy in (-3.4,3.4):ctx.box('Culvert_abutment',x,y+dy,z+1,1.8,.65,1.1,sh.bp.STONE)
        ctx.box('Culvert_stone_lintel',x,y,z+2.5,1.9,4,.42,sh.bp.STONE)
        for xx,yy in [(sign*15,-15),(sign*18,-9),(sign*24,-15)]:ctx.rock(xx,yy,1.8)
    ctx.refuge(0,-13,83,15,.84,'Damp transverse drainage and stone culvert interrupt ground fire')
    # Ditch banks are composed in groups, not scattered across the landscape.
    for x in (-82,-68,-56,44,62,83):
        y=-12-8*math.sin(x/64)
        ctx.rock(x,y-6,1.2 if x%3 else 1.8)
    for x,y,h in [(-58,-31,28),(-76,-29,22),(-61,-45,20),(66,11,30),(79,20,23)]:ctx.tree(x,y,h,style='drainage')
    fence(ctx,[(-36,35),(-49,42),(-65,45),(-81,47)],True)
    wall(ctx,[(35,y) for y in range(-90,-39,5)])
    ctx.box('Crossing_marker',15,5,ctx.ground(15,5)+1.2,.65,.8,1.2,sh.bp.STONE)

def orchard(ctx):
    road(ctx)
    # Two legible cultivated rows occupy the broad outside of the elbow.
    # A shorter inside grove opens a clear view into the bend.
    for col,x in enumerate((-82,-58,-34)):
        for row,y in enumerate((-14,12,38,64)):
            ctx.tree(x+(2 if row%2 else -1),y,18+((row*3+col*2)%7),style='orchard')
    for x,y,h in [(54,-60,19),(77,-65,21),(94,-61,17),(75,-85,18)]:ctx.tree(x,y,h,style='orchard')
    wall(ctx,[(x,83) for x in range(-88,-20,5)])
    fence(ctx,[(-97,-29),(-96,-7),(-96,15),(-96,37),(-96,58)],False)
    ctx.refuge(-57,24,39,57,.58,'Cultivated orchard shelter behind stone field boundary')
    # Small open harvest barrow, grounded beside the orchard approach.
    x,y=-21,-39;z=ctx.ground(x,y);root=(x,y)
    for dx in (-2,2):
        timber(ctx,ctx.beam('Harvest_barrow_runner',(x+dx,y-4,z+.7),(x+dx,y+4,z+.7),.19),root,'runner')
    for yy in (-2,-.8,.4,1.6,2.8):
        timber(ctx,ctx.box('Harvest_barrow_plank',x,y+yy,z+1.15,2.3,.48,.13),root,'plank')
    for dx in (-2,2):
        timber(ctx,ctx.beam('Harvest_barrow_handle',(x+dx,y-4,z+.7),(x+dx,y-8,z+1.8),.14),root,'handle')
    for x,y,s in [(-93,82,2.4),(97,-82,1.8)]:ctx.rock(x,y,s)

def main():
    sh.init()
    specs=[
        dict(id='EF_ENTRY_WINDWARD_MEADOW',title='Windward Meadow',purpose='Quiet maintained-field entry protected by wall and gate',seed=1001,edges={'S':('HOLLOW',0),'N':('HOLLOW',0)},land=meadow_land,guide=sh.straight(5),landmark='Windward field wall and surviving meadow',grass_count=3400),
        dict(id='EF_DRAINAGE_CROSSING',title='Drainage Crossing',purpose='Shallow wet drainage with compact roadside stone culvert mouths',seed=1002,edges={'S':('HOLLOW',0),'N':('HOLLOW',0)},land=drainage_land,guide=sh.straight(3),landmark='Low stone-lintel culvert crossing',grass_count=2900,grass_filter=lambda x,y:abs(y+12+8*math.sin(x/64))>5),
        dict(id='EF_ORCHARD_BEND',title='Orchard Bend',purpose='Level right bend framed by cultivated orchard rows and short inside grove',seed=1003,edges={'S':('HOLLOW',0),'E':('HOLLOW',0)},land=orchard_land,guide=sh.turn('E'),landmark='Orchard rows framing road bend',grass_count=2800),
    ]
    contexts=[];rows=[]
    for spec,dress in zip(specs,(meadow,drainage,orchard)):
        ctx,row=sh.build(spec,dress);contexts.append(ctx);row['objects']-=1;row['triangles']-=512;row['review_road_excluded']=True;ctx.scene['Metadata']=json.dumps(row);rows.append(row)
    sh.finish_lane('countryside',rows,contexts)

if __name__=='__main__':main()
