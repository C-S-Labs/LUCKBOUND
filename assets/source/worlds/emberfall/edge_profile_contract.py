"""Isolated authored edge contract, in Blender/stud coordinates; no runtime edits.

Only source-local specs enter height(). Assembly transforms never enter it.
"""
import math

HALF = 128
DEPTH = 40
TOLERANCE = 0.01
SIGNS = {'HOLLOW': 1, 'CREST': -1}
SPECS = {
    'A': {'S': ('HOLLOW', -24), 'N': ('HOLLOW', 0), 'shape': 0},
    'A2': {'S': ('HOLLOW', 0), 'N': ('HOLLOW', 0), 'shape': 1},
    'B1': {'S': ('HOLLOW', 0), 'N': ('HOLLOW', 0), 'shape': 2},
    'B2': {'S': ('HOLLOW', 0), 'E': ('CREST', 24), 'shape': 3},
    'B3': {'W': ('HOLLOW', 0), 'N': ('HOLLOW', 0), 'shape': 4},
    'C': {'S': ('CREST', 0), 'N': ('CREST', 0), 'shape': 5},
}


def smooth(t):
    t = max(0, min(1, t))
    return t*t*(3-2*t)


def samples(kind):
    values = [SIGNS[kind]*12*smooth((abs(s)-16)/112) for s in range(-128,129,8)]
    # Zero endpoint derivative makes adjacent side/corner joins C1-compatible.
    values[1] = values[0]
    values[-2] = values[-1]
    return values


def profile(kind, s):
    v = samples(kind)
    p = max(0,min(32,(s+128)/8)); i = min(31,int(p))
    return v[i]+(v[i+1]-v[i])*(p-i)


def corner_heights(spec):
    corners = {}
    pairs = {'S': ('SW','SE'), 'N': ('NW','NE'), 'W': ('SW','NW'), 'E': ('SE','NE')}
    for side in pairs:
        if side not in spec: continue
        kind, datum = spec[side]
        for c in pairs[side]:
            value = datum+SIGNS[kind]*12
            if c in corners and abs(corners[c]-value)>TOLERANCE:
                raise ValueError('Incompatible authored corner '+c)
            corners[c] = value
    fallback = sum(corners.values())/len(corners)
    return {c: corners.get(c,fallback) for c in ('SW','SE','NW','NE')}


def edge(spec, side, s):
    if side in spec:
        kind, datum = spec[side]
        return datum+profile(kind,s)
    c = corner_heights(spec)
    a,b = {'S': ('SW','SE'), 'N': ('NW','NE'), 'W': ('SW','NW'), 'E': ('SE','NE')}[side]
    return c[a]+(c[b]-c[a])*smooth((s+128)/256)


def raw_height(name, x, y):
    spec = SPECS[name]; c = corner_heights(spec)
    u,v = smooth((x+128)/256),smooth((y+128)/256)
    # Source-authored Coons surface: preserves four fixed boundaries, including
    # corners. Unique interior landforms have no value/normal effect at edges.
    base = ((1-u)*edge(spec,'W',y)+u*edge(spec,'E',y)
            +(1-v)*edge(spec,'S',x)+v*edge(spec,'N',x)
            -((1-u)*(1-v)*c['SW']+u*(1-v)*c['SE']+(1-u)*v*c['NW']+u*v*c['NE']))
    k = spec['shape']
    envelope = smooth((128-abs(x))/DEPTH)*smooth((128-abs(y))/DEPTH)
    # Deliberately different source-local hills/drainage, not neighbour fitting.
    land = (7*math.sin(x/(62+3*k)+k*.7)*math.cos(y/(83-3*k))
            +3*math.sin(y/46+x/94+k)-3*math.exp(-((x+61-9*k)/25)**2))
    return base+envelope*land


def height(name, x, y):
    # Authoring convention: origin is terrain centre at ground level. Rebase the
    # source once, including socket datums; never change an assembled mesh.
    return raw_height(name,x,y)-raw_height(name,0,0)


def guide(name):
    if name == 'B2':
        return [(128-128*math.cos(t*math.pi/128),-128+128*math.sin(t*math.pi/128)) for t in range(65)]
    if name == 'B3':
        return [(-128+128*math.sin(t*math.pi/128),128-128*math.cos(t*math.pi/128)) for t in range(65)]
    return [(6*math.sin(math.pi*t/64)**3,-128+4*t) for t in range(65)]


def grid(name, step):
    n = 256//step+1
    vertices = [(x,y,height(name,x,y)) for y in range(-128,129,step) for x in range(-128,129,step)]
    faces = []
    for j in range(n-1):
        for i in range(n-1):
            a=j*n+i; faces.extend(((a,a+1,a+n+1),(a,a+n+1,a+n)))
    return vertices,faces


def surface(vertices, step, x, y):
    n = 256//step+1
    px=max(0,min(n-1,(x+128)/step)); py=max(0,min(n-1,(y+128)/step))
    i,j=min(n-2,int(px)),min(n-2,int(py)); u,v=px-i,py-j
    a=vertices[j*n+i][2]; b=vertices[j*n+i+1][2]
    c=vertices[(j+1)*n+i][2]; d=vertices[(j+1)*n+i+1][2]
    return a+(b-a)*u+(d-b)*v if u>=v else a+(d-c)*u+(c-a)*v


def socket(name, side):
    kind,datum=SPECS[name][side]
    x,z,facing={'S':(0,128,180),'N':(0,-128,0),'W':(-128,0,270),'E':(128,0,90)}[side]
    return {'Id': side, 'Kind': 'BP_EDGE_'+kind, 'OffsetX':x,'OffsetY':datum-raw_height(name,0,0),'OffsetZ':z,'Facing':facing,'Width':24}
