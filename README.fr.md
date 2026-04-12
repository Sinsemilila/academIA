<div align="center">

# Academie-IA

**Plateforme d'apprentissage des langues augmentee par IA**

![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit-FF3E00?logo=svelte&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Infra-Docker%20Compose-2496ED?logo=docker&logoColor=white)
![AI](https://img.shields.io/badge/AI-5%20LLMs%20via%20LiteLLM-8A2BE2)
![Self-Hosted](https://img.shields.io/badge/Deploy-Self--Hosted%20Proxmox-E57000)

[English](README.md) | Francais

</div>

---

## C'est quoi ?

Une plateforme d'apprentissage auto-hebergee qui utilise plusieurs modeles IA pour delivrer des lecons personnalisees et adaptatives. Construite pour un petit groupe d'amis apprenant l'anglais, avec une architecture pensee pour s'etendre a n'importe quelle langue ou domaine technique.

La plateforme retient les forces, faiblesses et le style d'apprentissage de chaque eleve entre les sessions.

## Fonctionnalites principales

- **Pedagogie TTT adaptative** — cycle Test-Teach-Test avec transitions de concepts deterministes
- **5 modeles LLM** routes via LiteLLM (Groq, Mistral, OpenAI) — 90% gratuit
- **Profils persistants** — scores de confiance par concept, streaks, XP, niveaux
- **Memoire a 2 niveaux** — snapshots de session + profils pedagogiques long-terme
- **Chat streaming temps reel** — SSE depuis Dify via FastAPI
- **PWA installable** — service worker, responsive mobile
- **Mode quiz/examen** — 10 questions avec LLM premium
- **6 utilisateurs actifs** avec profils individuels

## Stack technique

| Couche | Technologie |
|--------|------------|
| Frontend | SvelteKit + TypeScript (PWA) |
| Backend | FastAPI (Python) |
| Orchestration IA | Dify (Chatflow 28 noeuds) |
| Gateway LLM | LiteLLM (routing multi-modeles) |
| Workflows | n8n (memoire, profils) |
| Base de donnees | PostgreSQL |
| Infra | Docker Compose sur Proxmox |
| Securite | Cloudflare Zero Trust (WARP) |

## Architecture

Voir le [README anglais](README.md#architecture) pour le diagramme Mermaid complet.

```
Cloudflare Zero Trust → nginx → SvelteKit → FastAPI → Dify → LiteLLM → LLMs
                                                ↓
                                          PostgreSQL (profils, scores, XP)
```

## Lecons apprises

- **Groq gratuit est utilisable en prod** — Llama 3.3 70B gere l'enseignement anglais B1-C1 sans probleme
- **Dify Chatflows** = iteration rapide sur les prompts grace a l'editeur visuel
- **Le systeme de memoire a 2 niveaux** cree une experience convaincante "l'IA se souvient de moi"
- **On aurait du commencer avec PostgreSQL** au lieu d'explorer SQLite/JSON
- **Le detour Qdrant/Ollama etait inutile** — pas besoin de RAG pour le curriculum

---

<div align="center">

Construit avec curiosite par [Sinse](https://github.com/Sinsemilila) et une armee d'agents IA.

</div>
