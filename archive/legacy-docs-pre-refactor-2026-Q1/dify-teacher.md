---
summary: "Dify agents config, Teacher v17 chatflow architecture, system prompts"
read_when: "Modifying Teacher chatflow, Dify agents, or system prompts"
---

# Dify & Teacher — AcademIA

## Agents configured

Teacher (English, primary), Maestro (Spanish), Sensei (Japanese), Lehrer (German), Professore (Italian), PyMentor (Python), CyberMentor (Cybersec).

Only Teacher is fully operational with v17 chatflow.

## Teacher v17

- Type: Chatflow (advanced-chat)
- App ID: 39565197-c9d1-4d5b-b66f-18925de236d9
- Model: groq-standard (Llama 3.3 70B)
- Architecture: 28 nodes, 45 edges
- Source of truth: /opt/academia/scripts/update_teacher_chatflow.py

### Key nodes

- Start node: 3 inputs (minutes_since_last, mock_exam, mode_override)
- HTTP Request at start → dify-profil-get → profile injected via Jinja2
- code_turn_check: deterministic focus_concept + concept_modes + mock_exam parsing
- sys.user_id = Dify account UUID (not username)

### Exam mode

- Triggered by mock_exam input from webapp Quiz button
- Uses gpt-4o-mini (paid, higher quality)
- 10 questions, immediate feedback, final score

## Dify API access

- Admin key: `cat /opt/academia-shared/secrets/dify-admin-key`
- Workspace ID: [REDACTED-WORKSPACE-ID]
- Headers: `Authorization: Bearer <KEY>` + `X-WORKSPACE-ID: <ID>`

## User mapping

- sinse dify_user_id: [REDACTED-DIFY-UUID]
- sys.user_id in Chatflow = UUID of connected Dify account

## TODO

- Connect dify-snapshot in Teacher (every 10 interactions)
- Connect dify-profil-update at end of Teacher session
- Apply v2 system prompt + Chatflow to other agents
