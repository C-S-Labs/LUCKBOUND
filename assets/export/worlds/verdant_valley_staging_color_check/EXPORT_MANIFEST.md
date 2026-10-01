# Verdant Valley staging export manifest

Studio validation pending. Working exports untouched.

| Chunk | Category | Objects | Full destination |
|---|---|---:|---|
| chunk_path_cliff_passage | structure | 1 | `C:\Users\jhpel\LUCKBOUND\assets\export\worlds\verdant_valley_staging_color_check\path_cliff_passage_structure.fbx` |
| chunk_path_cliff_passage | solid_props | 1 | `C:\Users\jhpel\LUCKBOUND\assets\export\worlds\verdant_valley_staging_color_check\path_cliff_passage_solid_props.fbx` |
| chunk_path_cliff_passage | nonsolid_props | 1 | `C:\Users\jhpel\LUCKBOUND\assets\export\worlds\verdant_valley_staging_color_check\path_cliff_passage_nonsolid_props.fbx` |

## Owner testing direction — 2026-09-30

Missing/black colors and Cliff Passage structure appearance are deferred for initial functionality testing. Combined verdant_valley_structure.fbx and verdant_valley_props.fbx are alternatives to the per-chunk exports: do not activate both sets. Studio currently contains the combined models as well as individual imports. Keep individual imports active and park combined models outside Workspace before interpreting collision/visual test results. Preserve all models/files until owner validation; no cleanup performed.
