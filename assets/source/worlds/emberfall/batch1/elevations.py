"""Three frozen Burned Plains elevation sources; approved Batch 1 only.

Run through tools/run_blender.py. Burn appearance is assembly-owned; these
stressed-colour previews preserve root anchors and local protected pockets.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch1_shared as shared


def mound(x, y, cx, cy, rx, ry, height):
    return height * math.exp(-((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2)


def ridge_land(x, y):
    # A broad crest holds the route; a shallow east swale opens the overlook.
    return (mound(x, y, -23, 12, 65, 112, 4.5)
            - mound(x, y, 66, 18, 44, 76, 4.0)
            - mound(x, y, -81, -35, 24, 79, 2.2)
            + mound(x, y, 12, 66, 74, 37, 1.8))


def ridge_dress(ctx):
    # Unequal tree intervals and crown heights form a field windbreak, not rails.
    for x, y, h in [(-35, -79, 23), (-42, -44, 31), (-29, -9, 27),
                    (-39, 30, 33), (-48, 65, 21), (-74, 45, 18)]:
        ctx.tree(x, y, h=h, style='windbreak')
    ctx.wall([(-21, y) for y in (-64, -57, -50, -43)])
    ctx.wall([(-26, y) for y in (25, 32, 39)])
    for x, y, s in [(61, -37, 1.5), (74, -31, 2.3), (69, 66, 1.8)]:
        ctx.rock(x, y, s)
    ctx.refuge(-54, 23, 27, 59, .25,
               'Leeward grass behind the ridge windbreak and surviving field wall')


def switchback_land(x, y):
    # Earth banks rise gradually to the northwest; the outside bend stays broad.
    return (mound(x, y, -35, 8, 64, 73, 6.5)
            + mound(x, y, 38, 42, 73, 35, 3.2)
            - mound(x, y, 58, -75, 67, 28, 2.6)
            - mound(x, y, -47, -77, 30, 49, 1.8))


def switchback_dress(ctx):
    for x, y, h in [(-29, -67, 29), (-35, -27, 35), (-22, 17, 26),
                    (14, 33, 31), (53, 31, 23), (88, 28, 20),
                    (-76, 45, 17), (72, -83, 15)]:
        ctx.tree(x, y, h=h, style='cutbank_line')
    # Discontinuous field edge follows the old cutbank, outside the bend.
    ctx.wall([(-51, -43), (-48, -36), (-45, -29)])
    ctx.wall([(31, 53), (38, 55), (45, 55)])
    for x, y, s in [(-57, -17, 2.4), (-52, -11, 1.7), (40, 54, 1.5)]:
        ctx.rock(x, y, s)
    ctx.refuge(-47, -28, 25, 40, .22,
               'Sheltered lower bank at the foot of the cutbank tree line')


def terrace_land(x, y):
    # A low elongated ridgebench, open west grassland and asymmetric drainage.
    return (mound(x, y, 27, 10, 62, 91, 3.0)
            - mound(x, y, -60, -24, 47, 74, 2.3)
            - mound(x, y, 77, 48, 27, 57, 1.6)
            + mound(x, y, -32, 58, 59, 34, 1.4))


def terrace_dress(ctx):
    # One modest solid stone landmark. No enclosure, settlement or heroic scale.
    x, y = 24, 28
    root = ctx.ground(x, y)
    stone = shared.bp.STONE
    pieces = [ctx.box('Waymark_foot', x, y, root + .6, 2.7, 2.4, .6, stone),
              ctx.box('Waymark_plinth', x, y, root + 1.55, 1.9, 1.7, .35, stone),
              ctx.box('Waymark_standing_stone', x, y, root + 4.5, 1.05, .8, 2.6, stone),
              ctx.box('Waymark_cap', x, y, root + 7.3, 1.35, 1.0, .25, stone)]
    for obj in pieces:
        obj['LandmarkRole'] = 'stone_waymark'
        obj['LocalRoot'] = [x, y, root]
    for x, y, h in [(-71, -57, 18), (-84, 4, 24), (-58, 71, 20),
                    (57, -49, 16), (71, 65, 27)]:
        ctx.tree(x, y, h=h, style='ridgebench')
    ctx.wall([(-46, 54), (-39, 54), (-32, 54), (-25, 54)])
    for x, y, s in [(33, 34, 1.3), (30, 38, 1.1), (-75, 30, 1.8)]:
        ctx.rock(x, y, s)
    ctx.refuge(-44, 60, 31, 22, .2,
               'Small field remnant on the sheltered side of the low bench wall')


def main():
    shared.init()
    specs = [
        dict(id='EF_RIDGE_ASCENT', title='Ridge Ascent', seed=10531,
             purpose='Broad +24 straight ridge; west roadside windbreak and open east overlook combat zone',
             edges={'S': ('HOLLOW', -24), 'N': ('HOLLOW', 0)},
             land=ridge_land, guide=shared.straight(4), grass_count=3000,
             landmark='Uneven field windbreak along the rising ridge'),
        dict(id='EF_SWITCHBACK_BANK', title='Switchback Bank', seed=10532,
             purpose='Gradual +24 right turn beneath an earthen cutbank and tree line; open outside bend',
             edges={'S': ('HOLLOW', 0), 'E': ('CREST', 24)},
             land=switchback_land, guide=shared.turn('E'), grass_count=3000,
             landmark='Rising cutbank and curved countryside tree line'),
        dict(id='EF_WAYMARK_TERRACE', title='Waymark Terrace', seed=10533,
             purpose='Level ridgebench with a single modest stone waymark and broad west combat meadow',
             edges={'S': ('CREST', 0), 'N': ('CREST', 0)},
             land=terrace_land, guide=shared.straight(2), grass_count=3000,
             landmark=dict(type='stone_waymark', x=24, y=28, height=7.55)),
    ]
    rows, contexts = [], []
    for spec, dress in zip(specs, [ridge_dress, switchback_dress, terrace_dress]):
        ctx, row = shared.build(spec, dress)
        guide = row['guide']
        row['road_max_sampled_grade'] = max(
            abs(b[2] - a[2]) / math.hypot(b[0] - a[0], b[1] - a[1])
            for a, b in zip(guide, guide[1:]))
        row['road_end_rise'] = guide[-1][2] - guide[0][2]
        row['authoring_note'] = 'Frozen source; stressed preview only; assembly assigns burn state'
        rows.append(row)
        contexts.append(ctx)
    shared.finish_lane('elevations', rows, contexts)


if __name__ == '__main__':
    main()
