# PROJECT: spiritvale-site

**Status**: 🟢 Active · **Started**: 2026-05-25 · **Owner**: เจ้านาย (Tam4shii)

## WHY
เจ้านายเล่นเกม **SpiritVale** (Steam app 3918510) — อยาก host patch note ของเกมไว้ที่โดเมนตัวเอง (`spiritvale.tama.sh`) เพื่อใช้ผูกกับ Claude artifact (และอาจขยายเป็น community hub ในอนาคต)

## SUCCESS
- ✅ Artifact ของ Claude fetch `https://spiritvale.tama.sh/patch.json` ได้โดยไม่ติด CORS
- ✅ Update patch ใหม่ = แค่ commit + push → live ภายใน ~1 min
- ✅ Landing page เปิด browser แล้วเห็นได้ (เผื่อคนพิมพ์ตรง)

## STACK
- **Hosting**: Cloudflare Pages (free tier)
- **DNS**: Cloudflare (zone `tama.sh`)
- **Repo**: GitHub `Tam4shii/spiritvale-site` (public, no secrets)
- **Files**: static HTML + JSON + `_headers` (CORS)

## REPO
- URL: https://github.com/Tam4shii/spiritvale-site
- Branch: `main` (auto-deploy)

## INFRA
- CF Pages project: `spiritvale-site`
- Custom domain: `spiritvale.tama.sh` (CNAME → `spiritvale-site.pages.dev`)
- Zone ID: `25183c6035ca60f9e2e57ac277e65192` (tama.sh)

## DEPS
ไม่มี build step — pure static. ไม่มี dependency

## PHASE 0 (Now)
- [x] Local scaffold + `patch.json`
- [x] Push GitHub repo (patches/ structure + _redirects + immutable cache headers — 2026-05-25)
- [ ] Connect CF Pages (manual: dash.cloudflare.com → Pages → New → Connect GitHub → Tam4shii/spiritvale-site)
- [ ] Custom domain + DNS (manual: CF Pages → Custom domain → spiritvale.tama.sh)
- [ ] Fill in real artifact URL in `patches/v0.17.0.json` + `patches/latest.json` + `patch.json` (set `"url"` field — currently `null`, safe for clients to check `if patch.url`)
- [ ] Verify CORS from artifact

## FUTURE (ถ้าจะขยาย)
- [x] HTML patch viewer ที่ `/patch/` (built 2026-05-26 — full archive + per-section rendering; **live only after CF Pages is connected** — see Phase 0 above)
- [x] JSON Schema at `/schema/patch.json` (published 2026-05-26 — validates Added/Changed/Fixed/Removed contract; `$schema` wired into all `patches/*.json`)
- Build guides / class info
- Boss tracker / event calendar
- API endpoints อื่นๆ (เช่น `/builds`, `/items`)

## RISKS
- 🟡 **CF Pages free tier**: 500 builds/month, 100k requests/day — เยอะมากสำหรับ static, ไม่น่าจะถึง
- 🟡 **DNS propagation**: ~5 นาที หลังเพิ่ม CNAME
- 🟢 **No secrets in repo** — public repo ปลอดภัย

## NOTES
- เกม SpiritVale = playtest (เจ้านายเล่นมาตั้งแต่ ~2026-05-14, 3046+ นาที playtime)
- Patch note ตัวแรกที่ host = v0.17.0 "The Echoing Spire" (2026-05-25)
