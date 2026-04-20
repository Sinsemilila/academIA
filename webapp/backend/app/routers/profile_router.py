import json
import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..auth import get_current_user
from .. import database as db

router = APIRouter(tags=["profile"])

# ── Rank thresholds ───────────────────────────
RANKS = [
    (0,     "Debutant"),
    (200,   "Explorateur"),
    (500,   "Apprenti"),
    (1500,  "Praticien"),
    (5000,  "Expert"),
    (15000, "Maitre"),
]

# ── Badge definitions ─────────────────────────
BADGE_DEFS = [
    {"id": "perseverant",    "name": "Perseverant",    "icon": "fire",    "desc": "Streak de 10 jours",         "type": "streak",  "threshold": 10},
    {"id": "infatigable",    "name": "Infatigable",    "icon": "star",    "desc": "Streak de 30 jours",         "type": "streak",  "threshold": 30},
    {"id": "premier_exam",   "name": "Premier examen", "icon": "target",  "desc": "Passer un examen",           "type": "exams",   "threshold": 1},
    {"id": "promotion",      "name": "Promotion",      "icon": "rocket",  "desc": "Monter de niveau",           "type": "promo",   "threshold": 1},
    {"id": "perfectionniste","name": "Perfectionniste", "icon": "gem",     "desc": "Score d'examen >= 95",       "type": "score",   "threshold": 95},
    {"id": "assidu",         "name": "Assidu",          "icon": "books",   "desc": "20 sessions completees",     "type": "sessions","threshold": 20},
    {"id": "centurion",      "name": "Centurion",       "icon": "trophy",  "desc": "100 sessions completees",    "type": "sessions","threshold": 100},
    {"id": "explorateur_xp", "name": "Explorateur XP",  "icon": "sparkle", "desc": "Atteindre 500 XP",          "type": "xp",      "threshold": 500},
    {"id": "expert_xp",      "name": "Expert XP",       "icon": "diamond", "desc": "Atteindre 5000 XP",         "type": "xp",      "threshold": 5000},
]


def _get_rank(xp: int) -> dict:
    current_rank = RANKS[0]
    next_rank = RANKS[1] if len(RANKS) > 1 else None
    for i, (threshold, name) in enumerate(RANKS):
        if xp >= threshold:
            current_rank = (threshold, name)
            next_rank = RANKS[i + 1] if i + 1 < len(RANKS) else None
    return {
        "name": current_rank[1],
        "threshold": current_rank[0],
        "next_name": next_rank[1] if next_rank else None,
        "next_threshold": next_rank[0] if next_rank else None,
    }


_ISO_639_1_RE = re.compile(r"^[a-z]{2}$")


class L1Payload(BaseModel):
    l1: str = Field(..., min_length=2, max_length=2, description="ISO-639-1 2-letter code (lowercase)")
    l1_watch_enabled: bool = True


@router.get("/api/profile/l1")
async def get_l1(domain: str = "en", user: dict = Depends(get_current_user)):
    """Return the learner's L1 (user-global, from eleves) + watch toggle (per-domain).
    Defaults: fr / enabled. Sprint 5 D2: L1 lives on eleves, toggle on profils_eleves.
    """
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"l1": "fr", "l1_watch_enabled": True}
    async with db.pool.acquire() as conn:
        l1_val = await conn.fetchval(
            "SELECT l1 FROM eleves WHERE id = $1",
            eleve_id,
        )
        watch_row = await conn.fetchrow(
            """SELECT l1_watch_enabled FROM profils_eleves
               WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )
    return {
        "l1": l1_val or "fr",
        "l1_watch_enabled": bool(watch_row["l1_watch_enabled"]) if watch_row and watch_row["l1_watch_enabled"] is not None else True,
    }


@router.put("/api/profile/l1")
async def set_l1(payload: L1Payload, domain: str = "en", user: dict = Depends(get_current_user)):
    """Update the learner's L1 (user-global) + watch toggle (per-domain).
    Sprint 5 D2: L1 is user-global on eleves.l1. The watch toggle stays per-profile
    to allow toggling hints differently per target language.
    """
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=400, detail="No learner profile bound to this user.")
    l1 = payload.l1.lower()
    if not _ISO_639_1_RE.match(l1):
        raise HTTPException(status_code=422, detail="l1 must be ISO-639-1 lowercase (2 letters).")
    async with db.pool.acquire() as conn:
        # Update L1 on eleves (user-global)
        await conn.execute(
            "UPDATE eleves SET l1 = $1 WHERE id = $2",
            l1, eleve_id,
        )
        # Update watch toggle on profile (per-domain)
        result = await conn.execute(
            """UPDATE profils_eleves
               SET l1_watch_enabled = $1, updated_at = NOW()
               WHERE eleve_id = $2 AND domain = $3""",
            payload.l1_watch_enabled, eleve_id, domain,
        )
    if result.endswith(" 0"):
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return {"l1": l1, "l1_watch_enabled": payload.l1_watch_enabled}


@router.get("/api/profile/{domain}")
async def get_profile(domain: str, user: dict = Depends(get_current_user)):
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"niveau": None, "scores": {}, "points_forts": None,
                "lacunes": None, "mode_apprentissage": None,
                "next_level": None, "next_level_scores": {}}

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT niveau_global, points_forts, lacunes,
                      mode_apprentissage, derniere_session, examen_en_cours,
                      dernier_examen, nb_examens_niveau, plan_sessions,
                      details_par_competence, onboarding_completed_at
               FROM profils_eleves WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )
    if not row:
        return {"niveau": None, "scores": {}, "points_forts": None,
                "lacunes": None, "mode_apprentissage": None,
                "next_level": None, "next_level_scores": {}}

    niveau = row["niveau_global"]

    # Derive concept scores from error profile
    scores = await _derive_concept_scores(eleve_id, domain, niveau)

    # Get full concept list for this level (including untested at 0)
    next_niveau_map = {"A1":"A2","A2":"B1","B1":"B2","B2":"C1","C1":"C2"}
    next_niv = next_niveau_map.get(niveau)
    async with db.pool.acquire() as conn:
        ck_row = await conn.fetchval(
            "SELECT concept_keys FROM curriculums WHERE domain = $1 AND niveau = $2",
            domain, niveau)
        all_keys = ck_row if isinstance(ck_row, list) else json.loads(ck_row or "[]")
        next_keys = []
        if next_niv:
            nk_row = await conn.fetchval(
                "SELECT concept_keys FROM curriculums WHERE domain = $1 AND niveau = $2",
                domain, next_niv)
            next_keys = nk_row if isinstance(nk_row, list) else json.loads(nk_row or "[]")

    # Ensure all concepts are in scores (untested = 0)
    for k in all_keys:
        if k not in scores:
            scores[k] = 0

    # N+1 scores (only those with actual progress, for mode libre tracking)
    next_level_scores = {k: scores[k] for k in next_keys if scores.get(k, 0) > 0}

    concept_keys = all_keys
    mastered = sum(1 for s in scores.values() if s >= 80)
    total_expected = len(concept_keys) or 1

    # Progress = average score across current level concepts
    avg_score = sum(scores.get(k, 0) for k in all_keys) / total_expected if total_expected > 0 else 0
    progress_pct = round(avg_score)

    dernier_examen = row["dernier_examen"]
    if isinstance(dernier_examen, str):
        dernier_examen = json.loads(dernier_examen)

    details = row["details_par_competence"]
    if isinstance(details, str):
        details = json.loads(details)

    return {
        "niveau": niveau,
        "scores": scores,
        "concept_keys": concept_keys,
        "points_forts": row["points_forts"],
        "lacunes": row["lacunes"],
        "mode_apprentissage": row["mode_apprentissage"],
        "derniere_session": str(row["derniere_session"]) if row["derniere_session"] else None,
        "mastered": mastered,
        "total_expected": total_expected,
        "progress_pct": progress_pct,
        "dernier_examen": dernier_examen,
        "nb_examens_niveau": row["nb_examens_niveau"] or 0,
        "next_level": next_niv,
        "next_level_scores": next_level_scores,
        "plan_sessions": row["plan_sessions"],
        "details_par_competence": details,
        "onboarding_completed_at": row["onboarding_completed_at"].isoformat() if row["onboarding_completed_at"] else None,
    }


@router.get("/api/me/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    """Return a compact per-domain summary for the multi-agent overview.

    Combines `profils_eleves` (source of truth : real diagnostic + sessions) with a
    fallback on `learner_profiles.derived_tutor_hints.cefr_placement` (provisional
    QCM estimate) when `profils_eleves` is absent for a domain. Used by home + stats
    pages to show all active agents at a glance.
    """
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"agents": []}

    async with db.pool.acquire() as conn:
        pe_rows = await conn.fetch(
            """SELECT domain, niveau_global, derniere_session,
                      onboarding_completed_at
               FROM profils_eleves WHERE eleve_id = $1""",
            eleve_id,
        )
        lp_rows = await conn.fetch(
            """SELECT domain, derived_tutor_hints, completed_at
               FROM learner_profiles WHERE eleve_id = $1""",
            eleve_id,
        )
        # Sessions & minutes this week, grouped by agent_name (chat_router maps agent → domain)
        week_rows = await conn.fetch(
            """SELECT agent_name,
                      COUNT(*) AS sessions,
                      COALESCE(SUM(EXTRACT(EPOCH FROM (last_message_at - started_at))::int), 0) / 60 AS minutes
               FROM user_sessions
               WHERE user_id = $1 AND started_at >= NOW() - INTERVAL '7 days'
               GROUP BY agent_name""",
            user["id"],
        )
    agent_to_domain = {
        "teacher": "en", "maestro": "es", "professore": "it",
        "lehrer": "de", "sensei": "ja",
        # Post-langues agents (not yet domain-mapped in registry) skip silently.
    }
    week_by_domain: dict[str, dict] = {}
    for r in week_rows:
        d = agent_to_domain.get(r["agent_name"])
        if d:
            week_by_domain[d] = {"sessions": r["sessions"] or 0, "minutes": r["minutes"] or 0}

    by_domain: dict[str, dict] = {}
    for r in pe_rows:
        by_domain[r["domain"]] = {
            "domain": r["domain"],
            "niveau": r["niveau_global"],
            "provisional": False,
            "source": "profils_eleves",
            "derniere_session": str(r["derniere_session"]) if r["derniere_session"] else None,
            "onboarding_completed_at": r["onboarding_completed_at"].isoformat() if r["onboarding_completed_at"] else None,
        }
    for r in lp_rows:
        d = r["domain"]
        hints = r["derived_tutor_hints"]
        if isinstance(hints, str):
            hints = json.loads(hints)
        cefr = (hints or {}).get("cefr_placement")
        if d not in by_domain and cefr:
            # No real profile yet — fall back to QCM estimate (provisional).
            by_domain[d] = {
                "domain": d,
                "niveau": cefr,
                "provisional": True,
                "source": "learner_profiles",
                "derniere_session": None,
                "onboarding_completed_at": r["completed_at"].isoformat(),
            }

    # Compute progress_pct per domain using the same formula as /api/profile/{domain}.
    for d, info in by_domain.items():
        niveau = info["niveau"]
        if not niveau or info["provisional"]:
            info["progress_pct"] = 0
            info["mastered"] = 0
            info["total_expected"] = 0
        else:
            scores = await _derive_concept_scores(eleve_id, d, niveau)
            async with db.pool.acquire() as conn:
                ck_row = await conn.fetchval(
                    "SELECT concept_keys FROM curriculums WHERE domain = $1 AND niveau = $2",
                    d, niveau,
                )
            all_keys = ck_row if isinstance(ck_row, list) else (json.loads(ck_row) if ck_row else [])
            total = len(all_keys) or 1
            avg = sum(scores.get(k, 0) for k in all_keys) / total
            info["progress_pct"] = round(avg)
            info["mastered"] = sum(1 for k in all_keys if scores.get(k, 0) >= 80)
            info["total_expected"] = len(all_keys)
        # Weekly activity per agent (always attached, even if 0)
        week = week_by_domain.get(d, {"sessions": 0, "minutes": 0})
        info["sessions_this_week"] = int(week["sessions"])
        info["minutes_this_week"] = int(week["minutes"])

    return {"agents": list(by_domain.values())}


async def _derive_concept_scores(eleve_id: int, domain: str, niveau: str) -> dict:
    """Per-concept scores: scores_confiance (n8n LLM) primary, error-profile family fallback."""
    import json as _json

    # Primary: scores_confiance maintained by n8n snapshot workflow (per-concept LLM eval)
    async with db.pool.acquire() as conn:
        sc_raw = await conn.fetchval(
            "SELECT scores_confiance FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
            eleve_id, domain)

    scores = {}
    if sc_raw:
        sc = sc_raw if isinstance(sc_raw, dict) else _json.loads(sc_raw or "{}")
        for key, data in sc.items():
            if isinstance(data, dict) and "score" in data:
                scores[key] = data["score"]

    # Fallback: error-profile family-level for concepts not yet in scores_confiance
    from .error_analysis_router import _build_error_profile
    profile = await _build_error_profile(eleve_id, domain)
    for key, score in profile.get("concept_scores", {}).items():
        if key not in scores:
            scores[key] = score

    return scores


@router.get("/api/streak")
async def get_streak(user: dict = Depends(get_current_user)):
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM streaks WHERE user_id = $1", user["id"]
        )
    if not row:
        return {"current_streak": 0, "longest_streak": 0, "total_sessions": 0}
    return {
        "current_streak": row["current_streak"],
        "longest_streak": row["longest_streak"],
        "total_sessions": row["total_sessions"],
    }


_DOMAIN_TO_AGENT = {
    "en": "teacher", "es": "maestro", "it": "professore",
    "de": "lehrer", "ja": "sensei",
}


@router.get("/api/stats/weekly")
async def get_weekly_stats(domain: str = "en", user: dict = Depends(get_current_user)):
    """Sessions + minutes + concepts stats for the last 7 days, scoped to the
    agent matching `domain` (so switching agent in the sidebar refreshes the row)."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"sessions": 0, "concepts": 0, "minutes": 0}

    user_id = user["id"]
    agent_name = _DOMAIN_TO_AGENT.get(domain)
    async with db.pool.acquire() as conn:
        if agent_name:
            sessions = await conn.fetchval(
                """SELECT COUNT(*) FROM user_sessions
                   WHERE user_id = $1 AND agent_name = $2
                     AND started_at >= NOW() - INTERVAL '7 days'""",
                user_id, agent_name,
            )
            minutes_val = await conn.fetchval(
                """SELECT COALESCE(SUM(EXTRACT(EPOCH FROM (last_message_at - started_at))::int), 0) / 60
                   FROM user_sessions WHERE user_id = $1 AND agent_name = $2
                     AND started_at >= NOW() - INTERVAL '7 days'""",
                user_id, agent_name,
            )
        else:
            sessions = 0
            minutes_val = 0
        minutes = minutes_val or 0

        # Count concepts with score > 0 (worked on) — scoped to domain
        row = await conn.fetchrow(
            """SELECT scores_confiance FROM profils_eleves
               WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )
        concepts = 0
        if row and row["scores_confiance"]:
            sc = row["scores_confiance"]
            if isinstance(sc, str):
                sc = json.loads(sc)
            concepts = sum(1 for v in sc.values()
                          if (v.get("score", 0) if isinstance(v, dict) else v) > 0)

    return {
        "sessions": sessions or 0,
        "concepts": concepts,
        "minutes": minutes,
    }


@router.get("/api/me/concepts")
async def get_concepts(domain: str = "en", user: dict = Depends(get_current_user)):
    """Return detailed concept scores grouped by module."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"niveau": None, "groups": {}, "scores": {}}

    async with db.pool.acquire() as conn:
        # Profile data
        row = await conn.fetchrow(
            """SELECT niveau_global
               FROM profils_eleves WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )
        if not row or not row["niveau_global"]:
            return {"niveau": None, "groups": {}, "scores": {}}

        niveau = row["niveau_global"]

        # Derive scores from error profile
        derived = await _derive_concept_scores(eleve_id, domain, niveau)
        scores = {}
        for k, v in derived.items():
            scores[k] = {"score": v, "last_seen": None}

        # Curriculum data (groups + weights)
        cur = await conn.fetchrow(
            """SELECT concept_keys, concept_groups, concept_weights
               FROM curriculums WHERE domain = $1 AND niveau = $2""",
            domain, niveau,
        )
        concept_keys = []
        concept_groups = {}
        concept_weights = {}
        if cur:
            concept_keys = cur["concept_keys"] if isinstance(cur["concept_keys"], list) else json.loads(cur["concept_keys"] or "[]")
            cg = cur["concept_groups"]
            concept_groups = cg if isinstance(cg, dict) else json.loads(cg or "{}")
            cw = cur["concept_weights"]
            concept_weights = cw if isinstance(cw, dict) else json.loads(cw or "{}")

    # Compute module insights
    full_scores = {}
    for k, v in scores.items():
        full_scores[k] = {
            "score": v.get("score", 0) if isinstance(v, dict) else v,
            "last_seen": v.get("last_seen") if isinstance(v, dict) else None,
            "days_seen": 0,
        }

    insights = {}
    for group_name, group_concepts in concept_groups.items():
        g_scores = [full_scores.get(c, {"score": 0, "last_seen": None, "days_seen": 0}) for c in group_concepts]
        g_mastered = [c for c, s in zip(group_concepts, g_scores) if s["score"] >= 80]
        g_weak = [(c, s) for c, s in zip(group_concepts, g_scores) if 0 < s["score"] < 50]
        g_medium = [(c, s) for c, s in zip(group_concepts, g_scores) if 50 <= s["score"] < 80]
        g_untested = [c for c, s in zip(group_concepts, g_scores) if s["score"] == 0]
        total = len(group_concepts)

        # Check for overdue concepts (not seen in 14+ days)
        overdue = []
        today_str = str(date.today())
        for c, s in zip(group_concepts, g_scores):
            ls = s.get("last_seen")
            if ls and s["score"] > 0:
                try:
                    last = date.fromisoformat(str(ls)[:10])
                    days_ago = (date.today() - last).days
                    if days_ago >= 14:
                        overdue.append((c, days_ago))
                except (ValueError, TypeError):
                    pass

        pretty = lambda c: c.replace("_", " ")

        if len(g_mastered) == total:
            insights[group_name] = "Module maitrise ! Continue les revisions espacees pour maintenir."
        elif len(g_untested) == total:
            insights[group_name] = "Module pas encore explore. Il sera couvert dans tes prochaines sessions."
        elif overdue:
            c_name, days = overdue[0]
            insights[group_name] = f"Attention : {pretty(c_name)} n'a pas ete revu depuis {days} jours. Pense a le reviser."
        elif g_weak:
            names = " et ".join([pretty(c) for c, _ in g_weak[:2]])
            insights[group_name] = f"Bonne progression mais {names} necessite encore du travail."
        elif g_untested and g_mastered:
            insights[group_name] = f"{len(g_mastered)}/{total} maitrise(s), {len(g_untested)} a decouvrir. Tu avances bien !"
        elif g_medium:
            names = " et ".join([pretty(c) for c, _ in g_medium[:2]])
            insights[group_name] = f"En bonne voie ! {names} se consolide, encore quelques sessions."
        else:
            insights[group_name] = "Continue ta progression sur ce module."

    # Concept tips — grammar rules, common mistakes, examples
    CONCEPT_TIPS = {
        "present_perfect_simple": {
            "rule": "have/has + participe passe. Relie le passe au present (experience, resultat actuel).",
            "mistake": "Utiliser le past simple avec 'already/yet/ever' → ces marqueurs exigent le present perfect.",
            "example": "I have visited Japan twice. / She hasn't finished yet.",
        },
        "present_perfect_vs_past_simple": {
            "rule": "Present perfect = lien avec le present. Past simple = moment precis revolu.",
            "mistake": "Dire 'I have seen him yesterday' → 'yesterday' = moment precis → past simple obligatoire.",
            "example": "I saw him yesterday (past simple). I have seen that film (experience, pas de date).",
        },
        "present_perfect_continuous": {
            "rule": "have/has been + -ing. Action commencee dans le passe qui continue ou vient de s'arreter.",
            "mistake": "Confondre avec le present perfect simple : 'I've been reading' (en cours) vs 'I've read 3 books' (resultat).",
            "example": "I've been waiting for 20 minutes. / It's been raining all day.",
        },
        "past_perfect": {
            "rule": "had + participe passe. Action terminee AVANT une autre action passee.",
            "mistake": "L'utiliser quand l'ordre chronologique est clair → inutile si 'then/after/before' suffit.",
            "example": "When I arrived, they had already left. / She had never seen snow before that day.",
        },
        "passive_voice": {
            "rule": "be + participe passe. Le sujet subit l'action au lieu de la faire.",
            "mistake": "Oublier de conjuguer 'be' au bon temps → 'The house was built' (past), 'is built' (present).",
            "example": "This bridge was built in 1890. / English is spoken worldwide.",
        },
        "conditional_1": {
            "rule": "If + present simple → will + base. Situation reelle et probable.",
            "mistake": "Mettre 'will' dans la partie 'if' → JAMAIS 'If I will go' → 'If I go, I will...'",
            "example": "If it rains, I'll stay home. / If you study, you will pass.",
        },
        "conditional_2": {
            "rule": "If + past simple → would + base. Situation irreelle ou improbable.",
            "mistake": "Dire 'If I would have' → c'est 'If I had'. Le 'would' va dans le resultat, pas la condition.",
            "example": "If I had more time, I would travel. / If I were you, I would accept.",
        },
        "modal_deduction": {
            "rule": "must = quasi certain, might/may = possible, can't = impossible.",
            "mistake": "Confondre 'must' (deduction) avec 'must' (obligation) → contexte crucial.",
            "example": "She must be tired (= j'en suis sur). He can't be French (= impossible).",
        },
        "reported_speech": {
            "rule": "Reculer d'un temps : present → past, past → past perfect, will → would.",
            "mistake": "Oublier de changer les pronoms et marqueurs de temps (today → that day, here → there).",
            "example": "'I am happy' → He said he was happy. / 'I will come' → She said she would come.",
        },
        "indirect_questions": {
            "rule": "Ordre sujet-verbe normal (pas d'inversion). Pas de 'do/does/did'.",
            "mistake": "Dire 'Can you tell me where is he?' → 'Can you tell me where he is?'",
            "example": "Do you know what time it is? / Could you tell me where the station is?",
        },
        "phrasal_verbs": {
            "rule": "Verbe + particule(s) qui changent le sens. A memoriser en contexte.",
            "mistake": "Traduire mot a mot depuis le francais → 'look for' ≠ 'regarder pour'.",
            "example": "Look up (chercher), give up (abandonner), turn off (eteindre), carry on (continuer).",
        },
        "gerund_vs_infinitive": {
            "rule": "Certains verbes → gerund (-ing), d'autres → infinitif (to). Listes a connaitre.",
            "mistake": "Dire 'I enjoy to read' → enjoy, avoid, finish, mind, suggest → toujours + -ing.",
            "example": "I enjoy reading (gerund). I want to read (infinitive). I stopped smoking / to smoke (sens different !).",
        },
        "relative_clauses": {
            "rule": "who (personnes), which (choses), that (les deux), where (lieux), whose (possession).",
            "mistake": "Utiliser 'what' au lieu de 'that/which' → 'The book what I read' → 'The book that I read'.",
            "example": "The woman who lives next door. / The car which was stolen. / That's the house where I grew up.",
        },
        "connectors": {
            "rule": "although/however = opposition, despite + nom/-ing, moreover/furthermore = ajout.",
            "mistake": "Confondre 'although' (+ phrase) et 'despite' (+ nom) → 'Despite he was tired' → 'Despite being tired'.",
            "example": "Although it was late, we continued. However, the results were disappointing.",
        },
        "used_to": {
            "rule": "used to + base = habitude passee qui n'existe plus. Forme negative : didn't use to.",
            "mistake": "Confondre 'used to do' (habitude passee) et 'be used to doing' (etre habitue a).",
            "example": "I used to smoke (= je fumais, plus maintenant). I'm used to driving (= j'ai l'habitude).",
        },
        "would_habitual": {
            "rule": "would + base pour decrire des habitudes passees repetees (narration, souvenirs).",
            "mistake": "Utiliser 'would' pour des etats → 'I would live there' est faux → 'I used to live there'.",
            "example": "Every summer, we would go to the beach. My grandmother would always sing.",
        },
        "adj_prepositions": {
            "rule": "Chaque adjectif a sa preposition fixe. A memoriser : good at, interested in, afraid of...",
            "mistake": "Calquer du francais → 'good in' (bon en) → 'good at'. 'Depend of' → 'depend on'.",
            "example": "I'm good at maths. She's interested in art. He's afraid of spiders.",
        },
        "adverbs_degree": {
            "rule": "quite/rather/fairly = modere. Extremely/absolutely = fort. Pretty = familier.",
            "mistake": "Utiliser 'very' avec des adjectifs extremes → 'very excellent' → 'absolutely excellent'.",
            "example": "It's quite interesting. The film was rather boring. She's extremely talented.",
        },
        "so_such_that": {
            "rule": "so + adjectif/adverbe. such + (a/an) + nom. Les deux → that pour la consequence.",
            "mistake": "Dire 'It was such hot' → 'It was so hot' (adjectif seul = so). 'Such a hot day' (avec nom = such).",
            "example": "It was so cold that we stayed inside. She's such a good singer that everyone loves her.",
        },
        "both_either_neither": {
            "rule": "both...and (les deux), either...or (l'un ou l'autre), neither...nor (ni l'un ni l'autre).",
            "mistake": "Verbe au pluriel apres 'neither' → 'Neither of them are' → 'Neither of them is' (singulier formel).",
            "example": "Both Tom and Jerry came. Either you stay or you leave. Neither she nor I was invited.",
        },
    }

    # Build personalized tips per concept
    concept_tips = {}
    for k in concept_keys:
        base = CONCEPT_TIPS.get(k)
        if not base:
            continue
        sc_data = full_scores.get(k, {"score": 0, "last_seen": None, "days_seen": 0})
        sc = sc_data["score"]
        tip = {**base}
        # Add personalized advice based on score
        if sc == 0:
            tip["advice"] = "Concept pas encore travaille. Il sera couvert en session."
        elif sc < 30:
            tip["advice"] = "Tu decouvres ce concept. Relis la regle et refais des exercices."
        elif sc < 50:
            tip["advice"] = "Les bases sont la mais fragiles. Concentre-toi sur le piege courant."
        elif sc < 80:
            tip["advice"] = "Bonne comprehension ! Varie les contextes pour consolider."
        else:
            tip["advice"] = "Bien maitrise. Reviens de temps en temps pour ne pas oublier."
        concept_tips[k] = tip

    return {
        "niveau": niveau,
        "concept_keys": concept_keys,
        "groups": concept_groups,
        "weights": concept_weights,
        "scores": scores,
        "insights": insights,
        "concept_tips": concept_tips,
    }


@router.get("/api/me/history")
async def get_history(domain: str = "en", limit: int = 20, user: dict = Depends(get_current_user)):
    """Return recent session snapshots."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"sessions": []}

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, contenu, created_at
               FROM snapshots_session
               WHERE eleve_id = $1 AND domain = $2
               ORDER BY created_at DESC LIMIT $3""",
            eleve_id, domain, limit,
        )

    sessions = []
    for r in rows:
        sessions.append({
            "id": r["id"],
            "summary": r["contenu"],
            "date": r["created_at"].isoformat(),
        })

    return {"sessions": sessions}


@router.get("/api/me/exams")
async def get_exams(domain: str = "en", user: dict = Depends(get_current_user)):
    """Return exam history from dernier_examen JSONB."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"current_exam": None, "last_exam": None}

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT examen_en_cours, dernier_examen, nb_examens_niveau
               FROM profils_eleves WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )

    if not row:
        return {"current_exam": None, "last_exam": None, "nb_exams": 0}

    current_exam = row["examen_en_cours"]
    if isinstance(current_exam, str):
        current_exam = json.loads(current_exam) if current_exam else None

    last_exam = row["dernier_examen"]
    if isinstance(last_exam, str):
        last_exam = json.loads(last_exam) if last_exam else None

    return {
        "current_exam": current_exam,
        "last_exam": last_exam,
        "nb_exams": row["nb_examens_niveau"] or 0,
    }


@router.get("/api/me/xp")
async def get_xp(user: dict = Depends(get_current_user)):
    """Return XP total, rank, and recent log."""
    user_id = user["id"]

    async with db.pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM xp_log WHERE user_id = $1",
            user_id,
        )
        recent = await conn.fetch(
            """SELECT amount, reason, agent_name, created_at
               FROM xp_log WHERE user_id = $1
               ORDER BY created_at DESC LIMIT 10""",
            user_id,
        )

    rank = _get_rank(total)
    return {
        "total": total,
        "rank": rank,
        "recent": [
            {
                "amount": r["amount"],
                "reason": r["reason"],
                "agent": r["agent_name"],
                "date": r["created_at"].isoformat(),
            }
            for r in recent
        ],
    }


@router.get("/api/me/xp-history")
async def get_xp_history(user: dict = Depends(get_current_user)):
    """Return cumulative XP over the last 30 days for progression graph."""
    from datetime import date, timedelta
    user_id = user["id"]
    start = date.today() - timedelta(days=29)

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT created_at::date as day, SUM(amount) as daily_xp
               FROM xp_log WHERE user_id = $1 AND created_at::date >= $2
               GROUP BY created_at::date ORDER BY day""",
            user_id, start,
        )

    # Build cumulative XP per day
    # First, get total XP before the period
    async with db.pool.acquire() as conn:
        base_xp = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM xp_log WHERE user_id = $1 AND created_at::date < $2",
            user_id, start,
        )

    daily_map = {str(r["day"]): r["daily_xp"] for r in rows}
    result = []
    cumulative = base_xp
    for i in range(30):
        d = str(start + timedelta(days=i))
        cumulative += daily_map.get(d, 0)
        result.append({"date": d, "value": cumulative})

    return {"data": result}


@router.get("/api/me/heatmap")
async def get_heatmap(user: dict = Depends(get_current_user)):
    """Return 180 days of activity data for heatmap."""
    from datetime import date, timedelta
    user_id = user["id"]
    start = date.today() - timedelta(days=179)

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT started_at::date as day, COUNT(*) as sessions, COALESCE(SUM(duration_seconds), 0) as seconds
               FROM user_sessions
               WHERE user_id = $1 AND started_at::date >= $2
               GROUP BY started_at::date ORDER BY day""",
            user_id, start,
        )
        # Also get streak activity from streaks table
        streak_days = await conn.fetch(
            """SELECT DISTINCT created_at::date as day FROM snapshots_session
               WHERE eleve_id = $1 AND created_at::date >= $2
               ORDER BY day""",
            user.get("eleve_id", 0), start,
        )

    # Build day map
    activity = {}
    for r in rows:
        activity[str(r["day"])] = {"sessions": r["sessions"], "minutes": r["seconds"] // 60}
    for r in streak_days:
        d = str(r["day"])
        if d not in activity:
            activity[d] = {"sessions": 1, "minutes": 15}  # snapshot = at least 1 session

    # Fill all 180 days
    days = []
    for i in range(180):
        d = str(start + timedelta(days=i))
        info = activity.get(d, {"sessions": 0, "minutes": 0})
        days.append({"date": d, **info})

    return {"days": days}


@router.get("/api/me/badges")
async def get_badges(domain: str = "en", user: dict = Depends(get_current_user)):
    """Compute which badges are unlocked based on live data."""
    user_id = user["id"]
    eleve_id = user.get("eleve_id")

    async with db.pool.acquire() as conn:
        # Streak data
        streak_row = await conn.fetchrow(
            "SELECT current_streak, longest_streak, total_sessions FROM streaks WHERE user_id = $1",
            user_id,
        )
        longest_streak = streak_row["longest_streak"] if streak_row else 0
        total_sessions = streak_row["total_sessions"] if streak_row else 0

        # XP total
        total_xp = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM xp_log WHERE user_id = $1",
            user_id,
        )

        # Exam + promo data
        nb_exams = 0
        best_score = 0
        nb_promos = 0
        if eleve_id:
            exam_row = await conn.fetchrow(
                """SELECT nb_examens_niveau, dernier_examen
                   FROM profils_eleves WHERE eleve_id = $1 AND domain = $2""",
                eleve_id, domain,
            )
            if exam_row:
                nb_exams = exam_row["nb_examens_niveau"] or 0
                de = exam_row["dernier_examen"]
                if isinstance(de, str):
                    de = json.loads(de) if de else None
                if de:
                    best_score = de.get("score", 0)
                    if de.get("passed"):
                        nb_promos = 1  # At least one promotion

    # Evaluate each badge
    badges = []
    for bd in BADGE_DEFS:
        progress = 0
        unlocked = False

        if bd["type"] == "streak":
            progress = min(longest_streak, bd["threshold"])
            unlocked = longest_streak >= bd["threshold"]
        elif bd["type"] == "sessions":
            progress = min(total_sessions, bd["threshold"])
            unlocked = total_sessions >= bd["threshold"]
        elif bd["type"] == "exams":
            progress = min(nb_exams, bd["threshold"])
            unlocked = nb_exams >= bd["threshold"]
        elif bd["type"] == "promo":
            progress = min(nb_promos, bd["threshold"])
            unlocked = nb_promos >= bd["threshold"]
        elif bd["type"] == "score":
            progress = min(best_score, bd["threshold"])
            unlocked = best_score >= bd["threshold"]
        elif bd["type"] == "xp":
            progress = min(total_xp, bd["threshold"])
            unlocked = total_xp >= bd["threshold"]

        badges.append({
            **bd,
            "unlocked": unlocked,
            "progress": progress,
        })

    return {"badges": badges}
