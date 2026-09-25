--!strict
-- Boss PREVIEWS for /showboss (debug only): look at a boss in its arena, in its idle pose/animation, to judge
-- whether the environment matches it. No health, attacks or AI - those come later.
--
-- Add a boss: import its FBX (rig + meshes) with the Studio 3D Importer, save the Model as
-- assets/rbxm/bosses/<Model>.rbxmx (Rojo maps that folder to ServerStorage.LuckboundBosses), upload its idle FBX
-- as an Animation (Animation Editor > Import > From FBX, then publish) and paste the id below. One row per boss.
--
--   Model  : the Model's name inside LuckboundBosses
--   Idle   : rbxassetid of the looping idle animation ("" = show the bind/rest pose)
--   Pose   : optional rbxassetid of a held pose (played frozen at its first frame instead of the idle)
--   Scale  : studs per Blender unit (enemies are authored in metres; ~2.8 puts a 1.8 m human at 5 studs)
--   Height : how far above the deck the rig's pivot sits (studs, after scaling); 0 if the pivot is at the feet

export type BossPreview = {
	Model: string,
	Idle: string,
	Pose: string?,
	Scale: number,
	Height: number,
}

return {
	winged_sentinel = { Model = "WingedSentinel", Idle = "", Scale = 2.8, Height = 0 },
} :: { [string]: BossPreview }
