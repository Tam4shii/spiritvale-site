# Changelog

All notable changes to SpiritVale are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
Machine-readable source: [`patches/index.json`](patches/index.json)

## [0.17.0] — The Echoing Spire  `2026-05-25`  *(current)*

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1833334318576172>

### Added
- The Echoing Spire (ET): 100-floor dungeon (monsters Lv100–200) — requires a Spire Key to create or enter an instance
- Spire Key crafting: 1 Resonance Core (0.1% drop from mobs / 1% from bosses) + 7 monster memories; memory cost increases per craft (7, 14, 21…) and resets weekly
- Monster memories: obtained by dismantling Cards and Gems
- Umbral Fragments: awarded to each party member per floor completed + extra drops from Spire bosses
- Dark Disciple NPC: sells new gear for Umbral Fragments (significant grind; Rebirth Essence useful here)
- ~7 new weapons and ~4 new armor pieces obtainable in the Spire
- Grimoires: new equip slot (up to 3 equipped at once), class-locked passives — trade in a full artifact set to receive one
- Base Class Grimoires: trade in box of origin sets with base class masters in Nevaris
- New Nevaris map: expanded, prettier, and more optimised (part of ongoing world map refresh by @Polliwagon)
- Boss lure crafting: craftsman NPC can craft boss lures in exchange for monster memories
- Vending Search: buy items in stacks of 10 or 100 (hold Ctrl or Shift respectively)
- New Server Selection UI with region indicators
- Click to Move toggle: disables the default click/hold-to-move character movement

### Changed
- Essence rarity order changed to Flow > Growth > Destruction > Rebirth > Chaos (rebalances Chaos imbalance)
- Chaos essence: implicit swap removed — higher chance for other options, much lower chance of nothing happening on non-weapons
- Rebirth essence: can now lock a stat while randomising the others (additional use case alongside original re-roll)
- Autocast reduced across the board: 20% → 10% and 30% → 20%; headgear autocast cards are now unique
- Bolts / Meteor / Chain Lightning autocast damage unnerfed: 50% → 100%
- Status damage reduced: divisor /8 → /10 (~20% reduction)
- Scrap Fang: Slots 4 → 3, Multistrike 100% → 50%
- Launcher: Slots 4 → 3
- Siphon reclassified as leech — recovery over time, capped at 20% HP/MP (was instant)
- Perfect Dodge: no longer scales with AGI, hard-capped at 95%
- Auto attacks can no longer hit the same target multiple times (fixes Launcher/Shotgun splash + chain overlap)
- Bosses recover 10% HP per second when out of combat (was 100% HP instantly)
- Shadow Step: cooldown 2 → 7 seconds (−1 per skill level)
- Sniper Shot: damage 150% → 200%
- Bosses: faster cast times, adjusted cooldowns, more targeted attacks, now spawn giant minions
- Shadow Step, Fireball, Ice Shard, Damnation, HolyWrath, Piercing Shot, and Sniper Shot can now be cast as either targeted or ground-targeted
- Utility items: Def/MDef stats replaced with weight limit per refine
- Monster flat Def scaling reduced: VIT/2 → VIT/5 (less impact on classes like Gunslinger)
- Atk% is now a separate multiplier (slightly more effective than before)
- Loot UI: moved and no longer clickable
- Cursor is now frozen during drag-rotation

### Fixed
- Skill mods not applying to summons
- Sacred Aegis not being refreshed correctly
- Several issues with monster leap attacks

### Removed
- Hidden 100% Multistrike removed from Naga, Bat, and Wolf gear

## [0.16.7] — Update 0.16.7  `2026-05-16`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1832700592795176>

### Changed
- Vending Search: double-clicking an item now lets you buy it directly
- Each account limited to 1 vending character (was 2)

### Fixed
- Damage numbers now optimised (major source of lag reduced)
- Server optimisations to reduce rubberbanding
- Vendors no longer huddle in a corner

### Removed
- Sell shops no longer visible on maps (purchase shops remain; sell shops may return in future)

## [0.16.3] — Update 0.16.3  `2026-05-13`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1832700592786579>

### Added
- 2 SEA servers (more EU / NA / SEA servers coming soon)
- Server list now auto-populates for future servers

### Fixed
- Rage skill not working on Berserker
- Vending list now automatically populates when opened

## [0.16.0] — Rebalance Patch  `2026-04-17`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1830163047261470>

### Added
- Threat System — monsters target the highest-threat player in range
- Spawner Bosses: 60s KS protection for the spawner and their party (cleared if spawner leaves map)

### Changed
- All class damage and sustain rebalanced using new metrics to reduce one-shots and full-heal spam
- Shared skills (Heal, Haste, Cure, FreeCast) removed from shared pool and redistributed to base classes
- Status effects revamped for clarity and to reduce status bloat
- All armor sets revamped (late-game armors were overpowering earlier sets)
- Monsters now have Def and Mdef stats
- Monster damage reduced by ~25%
- Boss regen removed
- Random boss casting and extra cast range removed

## [0.15.0] — PVP Systems and Status Immunities  `2026-03-24`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1827626365765818>

### Added
- PVP Skirmish Mode (free-for-all sandpit, now with NPC showing player count)
- Arena 2v2 and Arena 3v3 instanced modes (new map by Polliwagon)
- Arena rewards per match (more for wins), MMR calculation, and leaderboard
- Autoattack hotkey (default: C) — hold to continuously attack highlighted enemy
- Status Effect Immunity revamp — Attributes grant 2/3% resist per point to designated statuses

### Changed
- Pet loot pickup interval: 2s → 1s
- Gear swap blocked for 3s after dealing or receiving a hit
- Gunslinger Pistol/Shotgun range: 5 → 6; Gatling/Launcher: 8 → 9; Rifle: 10 → 12
- Flash Bang backslide range: 8 → 10; charges: 1 → 2
- Jump Shot range: 10 → 15
- Cards and gear grant 50% status resist (was 100%); Priest skills still grant 100%
- Silence durations reduced for Summoner, Priest, and Wizard
- Cure and Mass Cure can now be cast while Silenced
- Shinobi Fan of Knives now lands at cursor position (like Stomp)
- Gunk Shot and Wide Poison no longer apply Slow
- Inside PVP: all damage −75%, all healing −50%, summon stat inheritance halved, Revive forced to Lv.1
- Autoattack now starts after using a physical targeted attack skill

### Fixed
- Multiple PVP-related bug fixes
- Increased see-through-wall radius in most maps

## [0.14.0] — Cosmetics Update  `2026-03-15`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1826992588599147>

### Added
- Wardrobe and Cosmetics System — new in-game cosmetic menu
- Premium currency (p) purchased via Kofi donations (Steam purchase after EA release)
- Dozens of gear, pet, and mount cosmetics (mix of asset-pack and custom)
- Equip-to-cosmetic conversion (100p)
- Boss-exclusive cosmetics (boss drops)
- Monster-exclusive pets and mounts — tradable world drops
- Mystery Pet Box and Mystery Mount Box (world drops, give random monster pet/mount)
- Storage Expansion +500 slots (500p)
- New hair colors, eye colors, eye styles, and iris styles
- Character eye blinking animation
- Loot Filter (configurable in Settings)

### Changed
- Inventory and storage structures rebuilt for optimisation (one-time delay on first relog)
- Pets periodically pick up nearby items automatically
- Mounts grant 40% movement speed out of combat
- All premium cosmetics are account-bound; world-drop monster pets/mounts remain tradable
- Objects now become invisible near the player for visual clarity (most maps)

### Fixed
- Hair clipping through headgear greatly reduced
- Feet no longer clip through shoes

## [0.13.5] — Update 0.13.5  `2026-02-24`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1825093633196404>

### Changed
- Judgement Blade: now applies Slow on hit
- Divine Punishment: now applies Blind on hit
- Divine Punishment visual effects optimised
- Animation Delay now applied on cast instead of after cast for skills with cast times
- Minimum After Cast Delay: 0.14s → 0.3s
- Removed individual skill minimum cooldown of 0.3s (After Cast Delay now covers it)
- Movement slowed to 25% while Attacking/Casting (for first 33% of Animation Delay; unaffected by Free Cast)
- Shadow Seal, Shadow Feint, and Twist of Fate can now be cast while Silenced
- Unyielding and Blood Crash can now be cast while Silenced (and during Cyclone)
- Clones now copy toggle buffs upon being spawned

### Fixed
- Summons not casting Soul Strike with Invoker (Primary Summon only; by design)
- Gold not deducted when setting up a purchase shop
- Toggles resetting summon skills

## [0.13.2] — Update 0.13.2  `2026-02-20`

> Steam announcement: <https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1825093633187162>

### Changed
- Crafting and Refine cooldown: 0.7s → 0.1s
- Execute Axe: Cooldown −1 → −2, Damage 35% → 15% (now Exclusive)
- Chaos Reaver: Dark Claw Damage 35% → 15%
- Eclipse Kunai: Black Blade cooldown changed to Twist of Fate cooldown
- Fuma Shuriken: Removed skill mods, Slots 1 → 2
- Razor Kunai [Underground Cavern]: gained Fan of Knives and Shuriken Fan mods
- Stormfeather Kunai [Underground Cavern]: switched to melee substats
- Red Maw / Flintlock / Serpent Fang: Slots 3 → 2

### Fixed
- Database integration issues
- Healing not working against undead enemies
- Cooldown recovery stat not applying correctly
- Summon behaviour improved

---
*Generated from structured JSON — edit [`patches/v*.json`](patches/) to update.*
