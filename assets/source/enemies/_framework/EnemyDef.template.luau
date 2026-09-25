--!strict
-- EnemyDef template (STAGED: not wired into src/ until the owner approves the Studio integration).
-- One file per biome: src/shared/Content/Enemies/<Biome>.luau returning { [id]: EnemyDef }.
-- Shared services read these; no biome-specific enemy code. See docs/ENEMY_FRAMEWORK.md sections 3-6.

export type Marker = "Tell" | "HitStart" | "HitEnd" | "RecoverStart" | string

export type Move = {
	Action: string,            -- animation name, e.g. "P1_Lunge" (asset id in Animations)
	Damage: number,
	Range: number,             -- studs; the AI only picks the move inside this range
	Weight: number,            -- selection weight
	Cooldown: number,          -- seconds
	Hitbox: { Attachment: string, Size: Vector3 },
	RootMotion: { Distance: number, During: { Marker } }?,   -- AI-driven dash between markers
	FollowUps: { string }?,    -- combo continuations (still end in a recovery)
}

export type Phase = {
	HpBelow: number,           -- 1.0 = start
	Transition: string?,       -- action played on entry (invulnerable)
	Moves: { [string]: Move },
	DamageTakenMult: number?,  -- e.g. 1.25 once armour is shed
}

export type EnemyDef = {
	Id: string,
	Tier: "basic" | "miniboss" | "boss",
	Role: string,              -- archetype id (docs/ENEMY_FRAMEWORK.md section 3)
	Model: string,             -- rbxassetid / prefab path of the imported FBX
	Animations: { [string]: string },   -- action name -> animation asset id
	Stats: { Hp: number, Speed: number, Poise: number },
	Phases: { Phase },
	Vfx: { Palette: { Color3 }, Attachments: { [string]: string } },
}

local Example: EnemyDef = {
	Id = "winged_sentinel",
	Tier = "boss",
	Role = "boss",
	Model = "rbxassetid://0",
	Animations = { Idle_Guard = "rbxassetid://0", P2_Transition = "rbxassetid://0", P1_Lunge = "rbxassetid://0" },
	Stats = { Hp = 4000, Speed = 22, Poise = 3 },
	Phases = {
		{ HpBelow = 1.0, Moves = {
			DashLunge = { Action = "P1_Lunge", Damage = 18, Range = 24, Weight = 3, Cooldown = 2,
				Hitbox = { Attachment = "WeaponTip", Size = Vector3.new(2, 2, 6) },
				RootMotion = { Distance = 24, During = { "HitStart", "HitEnd" } } },
		} },
		{ HpBelow = 0.4, Transition = "P2_Transition", DamageTakenMult = 1.25, Moves = {} },
	},
	Vfx = { Palette = { Color3.fromHex("7FF6FF"), Color3.fromHex("9C7BD8") },
		Attachments = { Tip = "Weapon_R", Core = "VFX_Core", Eye = "VFX_Eye" } },
}

return { winged_sentinel = Example }
