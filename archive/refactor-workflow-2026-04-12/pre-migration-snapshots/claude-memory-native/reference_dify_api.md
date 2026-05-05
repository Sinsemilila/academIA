---
name: Dify API Access
description: Method to access Dify console API programmatically from cosmos
type: reference
---

## Accès API Dify Console (depuis cosmos)

```bash
ADMIN_KEY=$(cat /opt/academia-shared/secrets/dify-admin-key)

curl -s "http://127.0.0.1:5001/console/api/..." \
  -H "Authorization: Bearer $ADMIN_KEY" \
  -H "X-WORKSPACE-ID: <workspace-id>"
```

- Clé stockée dans : `/opt/academia-shared/secrets/dify-admin-key`
- IDs (app, workspace) : see project docs, not stored here

## Notes
- ADMIN_API_KEY_ENABLE=true configuré sur dify-api
- Secrets removed from this file — use `cat /opt/academia-shared/secrets/dify-admin-key`
