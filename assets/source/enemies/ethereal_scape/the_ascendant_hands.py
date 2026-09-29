# LUCKBOUND - The Ascendant's hands (manifest "extras", before the cloth). Its crystal fingers were built with two
# joints; hands_core gives every finger and thumb a third, so pose_fix.wrap() closes the hand round the Sanctum
# Staff's haft instead of hooking the fingertips onto it.
exec(open(FW + r"\hands_core.py").read())
add_phalanges()
