# Changelog

All notable changes to SpiritVale are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
Machine-readable source: [`patches/index.json`](patches/index.json)

## [0.17.0] — The Echoing Spire  `2026-05-25`  *(current)*

*Patch notes pending — see Steam announcement.*

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
