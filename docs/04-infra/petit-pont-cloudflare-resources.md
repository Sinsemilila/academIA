---
title: petit-pont.com Cloudflare resources reference
status: authoritative
last_reviewed: 2026-05-05
type: reference
tags: [infra, cloudflare, reference]
---

# petit-pont.com — Cloudflare resources reference

Source-of-truth des IDs CF (zones, account, apps, tunnel) pour automation. Tokens API stockés dans `secrets/shared.yaml.sops` (decrypt via `bash secrets/decrypt-shared.sh`).

## Account & zone

| Resource | Value |
|---|---|
| Account ID | `41f63b79c94d216d82c25565eac77701` |
| Account name | `Segura_clement@hotmail.fr's Account` |
| Zone petit-pont.com ID | `9f1fc98500f87d32bf3e8105bd8656fa` |
| Tunnel target | `a57431d7-9c36-4f9b-95b9-d3ef08b49691.cfargotunnel.com` |

## API tokens (sops keys)

| Sops key | Scope | Usage |
|---|---|---|
| `cloudflare-api-token-petit-pont` | Zone scoped petit-pont.com (DNS:Edit, Access:Edit, Zone:Edit) | DNS records, zone-level ops |
| `cloudflare-api-token-account` | Account-wide | Access apps + policies CRUD |

## Zero Trust Access apps (post-Phase 1 setup 2026-05-05)

| App | ID | Domain | Policy |
|---|---|---|---|
| academia.petit-pont.com | `a658bf89-e329-4a4c-902f-e5f142e75bcd` | academia.petit-pont.com | Sinse + Marie email |
| academia PWA bypass | `c53a02b9-e1d4-4e37-b696-f98b0eb9d64d` | academia.petit-pont.com/manifest.json | bypass-everyone |
| marie.petit-pont.com | `da7d8680-bc46-4a98-b193-04fe1e0c440f` | marie.petit-pont.com | Sinse + Marie email |
| coach.petit-pont.com | `86b21af3-386e-4b9b-94d4-9a4c8a9a007b` | coach.petit-pont.com | Sinse only (Bobby ajout futur Phase 6) |
| sinse.petit-pont.com | `c54a460e-160e-4915-b33b-9bbc59cf9356` | sinse.petit-pont.com | Sinse only |
| n8n.petit-pont.com | `b2d1e251-c99...` | n8n.petit-pont.com | (existing) |
| dify.petit-pont.com | `114eeba5-0ad...` | dify.petit-pont.com | (existing) |
| GlitchTip Dashboard | `f2427fde-973...` | glitchtip.petit-pont.com | (existing) |
| GlitchTip allauth bypass | `8cb62d51-7d7...` | glitchtip.petit-pont.com/_allauth | (existing) |
| GlitchTip SDK ingestion bypass | `fb947cba-331...` | glitchtip.petit-pont.com/api | (existing) |
| Accès Admin Proxmox | `6349e037-2d4...` | pve.petit-pont.com | (existing) |
| Warp Login App | `62b793d7-9c7...` | petitpont.cloudflareaccess.com/warp | (existing) |

## DNS records (CNAMEs vers tunnel)

academia, marie, coach, sinse, cosmos, dify, glitchtip, n8n, pve, ssh-cosmos, ssh-pve

academie.petit-pont.com supprimé 2026-05-05 (Phase 0.5 rename).

## Cosmos routes

| Hostname | Target |
|---|---|
| academia.petit-pont.com | `http://localhost:3001` (academia-frontend) |
| n8n.petit-pont.com | `http://localhost:5678` |
| dify.petit-pont.com | (cosmos managed) |
| glitchtip.petit-pont.com | `http://localhost:8001` |
| cosmos.petit-pont.com | self |

marie/coach/sinse pas encore routes Cosmos — Phase 2/4/5 ajoutera.
