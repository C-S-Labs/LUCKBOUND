# Body profile: generic creature (custom bone chains: wisps, drones, crawlers, eels, whales...).
# NO humanoid joint rules are applied. Only body-agnostic checks: clipping between pieces + grounding.
# If a creature needs its own joint behaviour (fins, tentacles, wings-as-arms), give it a custom profile instead.
exec(open(FW + r"\pose_common.py").read(), G)
BODY_PIECES = ()                           # set per creature if you want limb-vs-body clip checks
CLIP_PIECES = ()
def joint_report(tag=""): return []
def fix_clip(piece): pass
