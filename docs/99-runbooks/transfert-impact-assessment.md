# TIA — Transfer Impact Assessment (post-Schrems II)

**Status** : v1 — auto-évaluation alpha
**Last updated** : 2026-04-23
**Auteur** : Sinse (responsable de traitement)
**Révision** : annuelle ou à chaque changement de cadre légal US-UE
**Related** : [`dpia.md`](dpia.md), [`rgpd-registre.md`](rgpd-registre.md)

---

## 1. Contexte

Suite à l'arrêt **Schrems II** (CJUE C-311/18, 16 juillet 2020), les transferts de données personnelles vers les US doivent être encadrés par :
- une décision d'adéquation de la Commission européenne, **ou**
- des Clauses Contractuelles Types (SCC) accompagnées d'une analyse d'impact (TIA), **ou**
- des Règles d'entreprise contraignantes (BCR), **ou**
- une dérogation art. 49 RGPD.

Depuis le **10 juillet 2023**, la Commission a adopté une **décision d'adéquation pour le Data Privacy Framework (DPF)** : les transferts vers les organisations US auto-certifiées DPF sont considérés adéquats.

Ce document évalue les transferts US des sous-processeurs LLM utilisés par academie.petit-pont.com.

## 2. Liste des transferts

| Sous-processeur | Données transférées | Volume | Cadre légal |
|---|---|---|---|
| **OpenAI L.L.C.** (US) | Messages utilisateur (post-PII-scrubbing A5), prompt système Teacher/Maestro, output LLM | ~99% des appels chat | DPF (auto-certifié) + DPA OpenAI |
| **Groq Inc.** (US) | Idem OpenAI (fallback tier 2 quand quota gpt-4o-mini dépassé) | ~1% des appels chat | DPF (auto-certifié) + DPA Groq |
| **Google LLC** (AI Studio, US) | **Outputs Teacher uniquement** (pas de message learner) — judge Oracle pédagogique | Hors-bande, pas de chat user | DPF (auto-certifié) — DPA non disponible consumer-tier, risque accepté car pas de PII |
| **Cloudflare Inc.** (US/UE) | Trafic HTTP (IPs, user-agents, contenu cookies, payloads requêtes/réponses) — proxy en transit | 100% du trafic web | DPF (auto-certifié) + SCC standard auto-acceptés |

## 3. Analyse d'impact

### 3.1 Cadre légal des destinataires

Les 4 sous-processeurs (OpenAI, Groq, Google, Cloudflare) sont **auto-certifiés DPF** au [Data Privacy Framework Programme](https://www.dataprivacyframework.gov/list).

Vérifications effectuées (2026-04-23) :
- **OpenAI L.L.C.** : DPF active. À reconfirmer 1×/an.
- **Groq Inc.** : DPF active.
- **Google LLC** : DPF active.
- **Cloudflare Inc.** : DPF active + SCC contractuelles dans CDDA standard.

### 3.2 Risques résiduels malgré DPF

Le DPF couvre l'accès commercial mais des préoccupations subsistent (jurisprudence post-Schrems II, recours individuels possibles via DPRC) :

| Risque | Mitigation appliquée |
|---|---|
| **Accès gouvernemental US (FISA 702, EO 12333)** | DPF inclut le Data Protection Review Court (DPRC) pour recours. Volumétrie AcademIA = nano (~1 user actif), risque de surveillance ciblée nul. |
| **Réutilisation des données pour entraînement LLM** | OpenAI : opt-out training data activé via [console settings](https://platform.openai.com/account/data-controls). Groq : pas de training data par défaut. Gemini consumer-tier : risque résiduel **non scrubbable**, mitigé en limitant l'usage au judge Oracle (outputs synthétiques uniquement, pas de PII apprenant·e). |
| **Subpoena tier (DOJ, etc.)** | Pas d'évitement possible. Documentation claire dans CGU + politique de confidentialité. |
| **PII fuite via prompts** | A5 PII scrubber backend (regex email/téléphone/IBAN/NIR/CB → placeholders) avant envoi à tout LLM. |
| **Cross-user leak via injections de prompt** | A5 tests CI cross-user isolation (4 scénarios), 0 leak toléré. |

### 3.3 Évaluation par destinataire

#### OpenAI L.L.C.
- **DPF** : ✅ actif
- **DPA** : ⚠️ à signer self-service (Sinse, 2026-Q2)
- **Opt-out training** : ✅ activé compte org
- **Volumétrie** : ~99% du trafic chat
- **Verdict** : transfert légal, risque résiduel **faible** post-PII-scrubbing.

#### Groq Inc.
- **DPF** : ✅ actif
- **DPA** : ⚠️ à signer self-service (Sinse, 2026-Q2)
- **Training data** : ✅ pas par défaut
- **Volumétrie** : ~1% (fallback)
- **Verdict** : transfert légal, risque résiduel **faible**.

#### Google LLC (Gemini API consumer)
- **DPF** : ✅ actif
- **DPA** : ❌ pas disponible en consumer-tier
- **Données transmises** : outputs synthétiques Teacher uniquement (pas de message apprenant·e)
- **Verdict** : transfert légal sous DPF, **risque accepté** car aucune PII utilisateur ne transite. Pas d'usage chat user direct. À migrer vers Vertex AI (Workspace tier avec DPA) si on étend l'usage Gemini au chat user.

#### Cloudflare Inc.
- **DPF** : ✅ actif
- **DPA** : ✅ signé (TOS auto-accepté + CDDA SCC)
- **Données** : trafic web en transit, métadonnées (IP, headers)
- **Verdict** : transfert légal, risque résiduel **faible**. Cloudflare opère majoritairement depuis EU edge nodes pour le trafic FR.

## 4. Conclusion

Tous les transferts hors UE sont encadrés par le **DPF** (décision d'adéquation Commission européenne, 10 juillet 2023) — base juridique principale.

En complément :
- **DPA contractuels** signés pour les sous-processeurs où ils sont disponibles (Cloudflare ✅, OpenAI ⚠️ à faire, Groq ⚠️ à faire).
- **Mesures supplémentaires applicatives** : PII scrubber (A5), tests cross-user isolation (A5), opt-out training data (OpenAI).
- **Risque résiduel acceptable** pour une alpha privée fermée gratuite (≤10 testeurs, 0 commercialisation).

À réévaluer :
- **Avant ouverture publique payante** : signature DPO externe, audit juridique tier, contractualisation Vertex AI si on étend Gemini au chat user.
- **Si invalidation DPF** (recours en cours, jurisprudence à surveiller) : retomber sur SCC + mesures supplémentaires renforcées (chiffrement E2E payloads ?), évaluation alternatives EU-hosted (Mistral, Aleph Alpha).

## 5. Annexes

- [Décision d'adéquation DPF (Commission européenne, 2023-07-10)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023D1795)
- [DPF Programme — Liste des organisations US certifiées](https://www.dataprivacyframework.gov/list)
- [Schrems II — CJUE C-311/18](https://curia.europa.eu/juris/document/document.jsf?docid=228677)
- [`dpia.md`](dpia.md) §1.6, §3 pour les mesures de sécurité
- [`rgpd-registre.md`](rgpd-registre.md) §3 pour le détail sous-processeurs
