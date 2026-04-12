# Architecture — AcademIA

## Request flow (learner perspective)

```mermaid
sequenceDiagram
    participant U as Learner (browser)
    participant CF as Cloudflare
    participant NG as nginx
    participant SK as SvelteKit
    participant FA as FastAPI
    participant DI as Dify API
    participant LM as LiteLLM
    participant LLM as Groq/Mistral/OpenAI
    participant PG as PostgreSQL
    participant N8 as n8n

    U->>CF: HTTPS request
    CF->>NG: Tunnel (WARP verified)
    NG->>SK: Reverse proxy
    SK->>FA: /api/* proxy
    FA->>PG: Auth check + load profile

    rect rgb(240, 240, 255)
        Note over FA,LLM: Chat session (SSE streaming)
        FA->>DI: POST /chat-messages (stream)
        DI->>N8: GET profil-get (webhook)
        N8->>PG: Load profile + last snapshot
        N8-->>DI: Profile JSON
        DI->>LM: LLM request (with profile context)
        LM->>LLM: Route to best available model
        LLM-->>LM: Response stream
        LM-->>DI: Tokens
        DI-->>FA: SSE events
        FA-->>SK: SSE proxy
        SK-->>U: Real-time response
    end

    rect rgb(255, 240, 240)
        Note over DI,PG: Memory update (every 10 turns)
        DI->>N8: POST snapshot (webhook)
        N8->>LM: Summarize session (groq-snapshot)
        LM->>LLM: Llama 3.1 8B
        LLM-->>N8: Summary
        N8->>PG: Save snapshot
    end
```

## Memory system

```mermaid
graph LR
    subgraph "Level 1 — Session (short-term)"
        CONV[Conversation] -->|every 10 turns| SNAP[Snapshot]
        SNAP -->|rolling summary| SNAP
        SNAP -->|stored in| SS[(snapshots_session)]
    end

    subgraph "Level 2 — Profile (long-term)"
        SS -->|end of session| PROF[Profile Update]
        PROF -->|scores, strengths, gaps| PE[(profils_eleves)]
        PE -->|injected at start| CONV
    end
```

## Infrastructure

```
NAS (Synology)
└── Proxmox VE
    └── VM cosmos (Debian, 12GB RAM)
        ├── Docker Compose
        │   ├── academie-frontend (SvelteKit :3001)
        │   ├── academie-api (FastAPI :8000)
        │   ├── dify-web + dify-api + dify-worker + dify-sandbox
        │   ├── litellm-proxy (:4000)
        │   ├── postgres-academie (:5432)
        │   ├── redis-academie
        │   ├── n8n-academie (:5678)
        │   └── cosmos-server (reverse proxy)
        ├── nginx (:8080 → Cloudflare Tunnel)
        └── 2 SSDs: boot (50G) + data (850G)
```
