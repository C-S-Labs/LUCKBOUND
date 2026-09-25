--!strict
-- Boss PREVIEWS for /showboss (debug only): look at a boss in its arena, in its idle pose/animation, to judge
-- whether the environment matches it. No health, attacks or AI - those come later.
--
-- Add a boss: import its FBX (rig + meshes) with the Studio 3D Importer, save the Model as
-- assets/rbxm/bosses/<Model>.rbxmx (Rojo maps that folder to ServerStorage.LuckboundBosses), upload its idle FBX
-- as an Animation (Animation Editor > Import > From FBX, then publish) and paste the id below. One row per boss.
--
-- Animation ids are account/group-scoped like mesh ids (see assets/README.md -> "Set the Creator correctly"):
-- an Idle uploaded to one account fails silently (no error, animation just never plays) for anyone testing from
-- a different account or an unpublished place they own. See docs/PARTNER_SETUP.md -> "Animation and other
-- account-scoped ids" before assuming a boss preview is broken.
--
--   Model  : the Model's name inside LuckboundBosses
--   Idle   : rbxassetid of the looping idle animation ("" = show the bind/rest pose)
--   Pose   : optional rbxassetid of a held pose (played frozen at its first frame instead of the idle)
--   Tall   : the boss's standing height in STUDS. /showboss scales the model to this whatever size it imported
--            at (FBX unit handling varies), so never resize it in Studio. A player is ~5 studs.
--   Height : how far above the deck the rig's pivot sits (studs, after scaling); 0 if the pivot is at the feet

export type BossPreview = {
	Model: string,
	Idle: string,
	Pose: string?,
	Tall: number,
	Height: number,
	GlowColor: Color3?, -- Neon colour for the *Glow meshes (default citadel cyan)
}

return {
	winged_sentinel = {
		Model = "WingedSentinel",
		Idle = "rbxassetid://132590990835909",
		Tall = 16,
		Height = 0,
	}, -- owner-picked preview height (~3x a player)
} :: { [string]: BossPreview }
