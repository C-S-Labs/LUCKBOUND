# Emberfall linked review workspace

Open `E:/BlenderAIProjects/Projects/Emberfall/EmberfallMaster.blend`.
Use the scene selector and Numpad0 for its review camera:

- SourceCatalogue:17 frozen source chunks plus4 dressing variants; authored hidden collision linked alongside.
- AreaI: accepted Layout1/scenery presentation; source catalogue is editable-authority reference.
- AreaII_CastleB / AreaII_CastleA: approved continuous blockout, selected castle only.
- WholeWorld_B_PROVISIONAL / WholeWorld_A_PROVISIONAL: side-by-side montage; AreaI translated(-2200,0,0). **No approved seam, route or world placement.**

All mesh data remain library linked. Edit only the registered original area sources;
never create local overrides or make geometry local here. Cameras/lights/instance transforms
are master-owned review data. Collision collections retain authored visibility.
SceneryScaling's Layout1 is derived accepted presentation; its duplicated source chunks
are not editable authority. Master does not include hidden recovery alternatives.

[source_registry.json](source_registry.json) pins exact authoritative paths/hashes.
[master_validation.json](master_validation.json) records build/reopen checks.
Build script refuses an existing master; no source library is saved or rebuilt.
Run scripts only with the repository's tools/run_blender.py.
New master/renders are external runtime artifacts, not Git binaries. Preserve alongside
source backups before changing them. CastleVariantsContactSheet.png is in the same folder.
