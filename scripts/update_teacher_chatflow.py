#!/usr/bin/env python3
"""
Source de verite Teacher v14 — Cooldown module echoue (#5) + Mode revision lacunes (#6).

Changements v14 vs v13 :
  - #5 Cooldown module echoue : code_turn_check detecte dernier_examen.passed=False + sessions_since=0
    → plan_prefix guidance "consolider avant de repasser" + force concepts faibles
    Prerequis n8n : create_exam_scoring_workflow.py ajoute to_review[] dans dernierExamen
  - #6 Mode revision manuelle : PROMPT_SESSION detecte demande revision → [REVIEW_LACUNES]
    code_exam_detect detecte marker → review_mode_value="active"
    var_assigner_review_start (NEW) setconversation.review_mode
    code_turn_check : si review_mode="active" → override selected_concepts + plan_prefix revision
    Nouvelle conv var : review_mode (string, default "")

Noeuds geres (28) :
  code_profil_check, code_turn_check, code_check, code_eval_check,
  if_profil, if_first_turn, if_eval_ready, if_exam_active, if_exam_complete,
  if_resume_exam,
  llm_plan_choice, llm_session, llm_onboarding, llm_exam,
  code_exam_track, code_exam_detect, code_exam_bilan, code_exam_persist,
  answer_plan, answer_session, answer_onboarding, answer_exam, answer_exam_bilan,
  var_assigner, var_assigner_exam, var_assigner_exam_start, var_assigner_exam_reset,
  var_assigner_exam_resume, var_assigner_scoring_recovery, var_assigner_review_start (NEW),
  http_exam_scoring, http_exam_persist, http_scoring_recovery_clear

Edges : 45 au total.

Usage :
  python3 /opt/academie/scripts/update_teacher_chatflow.py && docker restart dify-api dify-worker
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"


def load_graph(workflow_id):
    result = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT graph FROM workflows WHERE id='{workflow_id}';"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout.strip())


def save_graph(workflow_id, graph):
    graph_json = json.dumps(graph, ensure_ascii=False)
    graph_sql = graph_json.replace("'", "''")
    sql = f"UPDATE workflows SET graph = '{graph_sql}'::json, updated_at = NOW() WHERE id = '{workflow_id}';"
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  [OK] {workflow_id}: {result.stdout.strip()}")
    else:
        print(f"  [ERR] {workflow_id}: {result.stderr.strip()}")


# ============================================================
# CODE NODES
# ============================================================

CODE_PROFIL_CHECK = r"""import json

def main(body: str) -> dict:
    if not body:
        return {
            "profil_present": False, "profil_text": "",
            "concept_keys_json": "[]", "scores_json": "{}",
            "mode_apprentissage": "libre",
            "next_concept_keys_json": "[]", "next_niveau": "",
            "examen_en_cours_json": "null",
            "dernier_examen_json": "null", "nb_examens_niveau": 0,
            "sessions_depuis_examen": 0,
            "concept_weights_json": "{}", "concept_groups_json": "{}",
            "derniere_session": ""
        }

    text = ""
    concept_keys = []
    scores = {}
    mode = "libre"
    next_keys = []
    next_niveau = ""
    examen_en_cours = None
    dernier_examen = None
    nb_examens = 0
    concept_weights = {}
    concept_groups = {}
    derniere_session = ""

    raw = str(body).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            text = parsed.get("profil_formate", "")
            concept_keys = parsed.get("concept_keys", [])
            scores = parsed.get("scores_confiance", {})
            mode = parsed.get("mode_apprentissage", "libre")
            next_keys = parsed.get("next_concept_keys", [])
            next_niveau = parsed.get("next_niveau", "")
            examen_en_cours = parsed.get("examen_en_cours", None)
            dernier_examen = parsed.get("dernier_examen", None)
            nb_examens = parsed.get("nb_examens_niveau", 0)
            sessions_depuis = parsed.get("sessions_depuis_examen", 0)
            concept_weights = parsed.get("concept_weights", {})
            concept_groups = parsed.get("concept_groups", {})
            derniere_session = parsed.get("derniere_session", "") or ""
    except (json.JSONDecodeError, TypeError):
        if raw.startswith('[PROFIL ELEVE]'):
            text = raw
        sessions_depuis = 0

    present = bool(text) and text.strip().startswith('[PROFIL ELEVE]')

    # --- Exam resume outputs ---
    exam_resume_mode = "off"
    exam_resume_question_num = 0
    exam_resume_responses = "[]"
    exam_resume_module_index = 0
    exam_resume_module_total = 1
    exam_resume_module_name = ""
    exam_resume_module_concepts = ""
    exam_resume_total_questions = 20
    exam_resume_modules_json = "[]"
    exam_resume_active = False
    exam_scoring_recovered = False

    if examen_en_cours and isinstance(examen_en_cours, dict):
        saved_mode = examen_en_cours.get("mode", "off")
        if saved_mode in ("active", "intro"):
            exam_resume_active = True
            exam_resume_mode = saved_mode
            exam_resume_question_num = int(examen_en_cours.get("question_num", 0))
            exam_resume_responses = str(examen_en_cours.get("responses", "[]"))
            exam_resume_module_index = int(examen_en_cours.get("module_index", 0))
            exam_resume_module_total = int(examen_en_cours.get("module_total", 1))
            exam_resume_module_name = str(examen_en_cours.get("module_name", ""))
            exam_resume_module_concepts = str(examen_en_cours.get("module_concepts", ""))
            exam_resume_total_questions = int(examen_en_cours.get("total_questions", 20))
            exam_resume_modules_json = str(examen_en_cours.get("modules_json", "[]"))
        elif saved_mode == "scoring":
            exam_scoring_recovered = True

    return {
        "profil_present": present,
        "profil_text": text,
        "concept_keys_json": json.dumps(concept_keys) if isinstance(concept_keys, list) else "[]",
        "scores_json": json.dumps(scores) if isinstance(scores, dict) else "{}",
        "mode_apprentissage": str(mode or "libre"),
        "next_concept_keys_json": json.dumps(next_keys) if isinstance(next_keys, list) else "[]",
        "next_niveau": str(next_niveau or ""),
        "examen_en_cours_json": json.dumps(examen_en_cours) if examen_en_cours else "null",
        "dernier_examen_json": json.dumps(dernier_examen) if dernier_examen else "null",
        "nb_examens_niveau": int(nb_examens or 0),
        "sessions_depuis_examen": int(sessions_depuis or 0),
        "concept_weights_json": json.dumps(concept_weights) if isinstance(concept_weights, dict) else "{}",
        "concept_groups_json": json.dumps(concept_groups) if isinstance(concept_groups, dict) else "{}",
        "exam_resume_active": exam_resume_active,
        "exam_resume_mode": exam_resume_mode,
        "exam_resume_question_num": exam_resume_question_num,
        "exam_resume_responses": exam_resume_responses,
        "exam_resume_module_index": exam_resume_module_index,
        "exam_resume_module_total": exam_resume_module_total,
        "exam_resume_module_name": exam_resume_module_name,
        "exam_resume_module_concepts": exam_resume_module_concepts,
        "exam_resume_total_questions": exam_resume_total_questions,
        "exam_resume_modules_json": exam_resume_modules_json,
        "exam_scoring_recovered": exam_scoring_recovered,
        "derniere_session": str(derniere_session or "")
    }
"""

CODE_TURN_CHECK = r"""import json
from datetime import datetime, timezone, date as date_type

# ── Helpers spaced repetition ──────────────────────────────────────────

def parse_score_entry(v):
    # Normalise ancien format (int) et nouveau ({score, last_seen, first_seen, days_seen})
    if isinstance(v, (int, float)):
        return int(v), None, 0
    if isinstance(v, dict):
        return int(v.get('score', 0)), v.get('last_seen'), int(v.get('days_seen', 0))
    return 0, None, 0

def expected_interval(score):
    # Jours attendus entre revisions selon le niveau de maitrise
    if score >= 90: return 30
    if score >= 70: return 14
    if score >= 50: return 7
    return 3

def compute_priority(score, last_seen_str, today):
    # Score de priorite : faible + ancien = urgent
    weakness = 100 - score
    if not last_seen_str:
        return weakness + 200
    try:
        ls = date_type.fromisoformat(str(last_seen_str)[:10])
        days = (today - ls).days
    except:
        days = 0
    interval = expected_interval(score)
    urgency = max(0, days - interval) * 2
    return weakness + urgency

def concept_label(key, score, last_seen_str, today, tag=None):
    # Label explicatif pour affichage dans le plan
    label = key.replace("_", " ")
    if tag:
        return label + " [" + tag + "]"
    if not last_seen_str:
        return label + " 🆕 jamais travaille"
    try:
        ls = date_type.fromisoformat(str(last_seen_str)[:10])
        days = (today - ls).days
    except:
        days = 0
    interval = expected_interval(score)
    overdue = days > interval * 1.5
    if overdue:
        weeks = days // 7
        if weeks >= 2:
            suffix = " ⏰ " + str(weeks) + " sem. sans revoir"
        elif days >= 7:
            suffix = " ⏰ 1 sem. sans revoir"
        else:
            suffix = " ⏰ " + str(days) + "j sans revoir"
    elif score < 50:
        suffix = " ⚡ score " + str(score)
    elif score >= 80:
        suffix = " ✅ " + str(score) + "/100"
    else:
        suffix = " (" + str(score) + "/100)"
    return label + suffix

# ── Main ───────────────────────────────────────────────────────────────

def main(dialogue_count: int, profil_text: str, concept_keys_json: str, scores_json: str,
         mode_apprentissage: str, next_concept_keys_json: str, next_niveau: str,
         exam_mode: str, dernier_examen_json: str, sessions_depuis_examen: int,
         concept_weights_json: str, concept_groups_json: str,
         examen_en_cours_json: str, exam_scoring_recovered: bool,
         review_mode: str, derniere_session: str,
         minutes_since_last: int,
         mock_exam: str, mode_override: str) -> dict:
    n = int(dialogue_count or 0)
    mode = str(mode_apprentissage or 'libre')
    # Mode override from frontend toggle (immediate effect)
    mode_over = str(mode_override or '').strip()
    if mode_over in ('structure', 'libre'):
        mode = mode_over
    exam = str(exam_mode or 'off')
    sessions_since = int(sessions_depuis_examen or 0)

    # --- SCORING RECOVERY : previous scoring failed ---
    scoring_recovery = False
    if exam == 'scoring':
        scoring_recovery = True
        exam = 'off'
    if bool(exam_scoring_recovered):
        scoring_recovery = True

    # --- EXAM RESUME : detect saved exam on first turn ---
    exam_resume_needed = False
    exam_resume_values = {}
    if n == 1:
        try:
            examen_ec = json.loads(examen_en_cours_json or 'null')
        except:
            examen_ec = None
        if examen_ec and isinstance(examen_ec, dict):
            saved_mode = examen_ec.get("mode", "off")
            if saved_mode in ("active", "intro"):
                exam_resume_needed = True
                exam = saved_mode

    niveau = 'B1'
    for line in (profil_text or '').split('\n'):
        if line.strip().startswith('Niveau : '):
            niveau = line.strip()[9:]
            break

    try:
        concept_keys = json.loads(concept_keys_json or '[]')
    except:
        concept_keys = []
    try:
        scores_raw = json.loads(scores_json or '{}')
    except:
        scores_raw = {}
    try:
        next_keys = json.loads(next_concept_keys_json or '[]')
    except:
        next_keys = []
    try:
        dernier_examen = json.loads(dernier_examen_json or 'null')
    except:
        dernier_examen = None
    try:
        weights = json.loads(concept_weights_json or '{}')
    except:
        weights = {}

    today = datetime.now(timezone.utc).date()

    # Normalise scores vers {concept: (score_int, last_seen_str|None, days_seen_int)}
    norm = {}
    for k, v in scores_raw.items():
        sc, ls, ds = parse_score_entry(v)
        norm[k] = (sc, ls, ds)

    scored_concepts = {k: norm[k][0] for k in concept_keys if k in norm}
    nb_total = len(concept_keys)

    untested = [k for k in concept_keys if k not in norm]
    weak = sorted([(k, v) for k, v in scored_concepts.items() if v < 50], key=lambda x: x[1])
    medium = sorted([(k, v) for k, v in scored_concepts.items() if 50 <= v < 80], key=lambda x: x[1])
    # Mastered = score >= 75 ET vu sur au moins 2 jours differents (consolidation memoire)
    mastered = [(k, v) for k, v in scored_concepts.items() if v >= 75 and norm[k][2] >= 2]
    # Score >= 75 mais pas encore consolide (moins de 2 jours)
    mastered_but_fresh = [(k, v) for k, v in scored_concepts.items() if v >= 75 and norm[k][2] < 2]

    promotion_ready = False
    exploring_next = False
    approaching_promo = False
    pct_mastered = (len(mastered) / nb_total * 100) if nb_total > 0 else 0

    all_tested = len(untested) == 0
    high_mastery = nb_total > 0 and len(mastered) >= nb_total * 0.8

    if all_tested and high_mastery:
        if mode == 'structure':
            promotion_ready = True
        else:
            exploring_next = True
    elif not all_tested and high_mastery:
        approaching_promo = True

    # --- COOLDOWN EXAMEN ---
    cooldown_met = True
    cooldown_reason = ""
    if promotion_ready and dernier_examen:
        exam_date_str = dernier_examen.get("date", "")
        days_since = 999
        if exam_date_str:
            try:
                exam_dt = datetime.fromisoformat(exam_date_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                days_since = (now - exam_dt).days
            except:
                days_since = 999

        need_days = days_since < 7
        need_sessions = sessions_since < 5

        if need_days or need_sessions:
            cooldown_met = False
            parts = []
            if need_days:
                parts.append(str(7 - days_since) + "j avant prochaine proposition")
            if need_sessions:
                parts.append(str(5 - sessions_since) + " sessions restantes")
            cooldown_reason = " + ".join(parts)

    selected = []

    if promotion_ready:
        all_sorted = sorted(scored_concepts.items(), key=lambda x: x[1])
        for k, v in all_sorted[:2]:
            selected.append(k)
    elif approaching_promo and untested:
        for k in untested:
            if len(selected) < 2:
                selected.append(k)
    elif exploring_next and next_keys:
        # Priorité par urgence spaced repetition sur niveau courant
        by_prio = sorted(
            [(k, compute_priority(scored_concepts.get(k, 0), norm.get(k, (0,None))[1], today))
             for k in concept_keys if k not in next_keys],
            key=lambda x: -x[1]
        )
        if by_prio:
            selected.append(by_prio[0][0])
        next_scores_norm = {k: norm[k][0] for k in next_keys if k in norm}
        next_untested = [k for k in next_keys if k not in norm]
        next_weak = sorted([(k, v) for k, v in next_scores_norm.items() if v < 50], key=lambda x: x[1])
        if next_untested:
            selected.append(next_untested[0])
        elif next_weak:
            selected.append(next_weak[0][0])
    else:
        # Sélection par priorité spaced repetition : weakness × urgence temporelle
        all_prio = []
        for k in concept_keys:
            if k in norm:
                sc, ls, _ds = norm[k]
                prio = compute_priority(sc, ls, today)
            else:
                prio = 300  # jamais testé = priorité max
            all_prio.append((k, prio))
        all_prio.sort(key=lambda x: -x[1])
        for k, _ in all_prio:
            if k not in selected:
                selected.append(k)
            if len(selected) >= 2:
                break

    # ── Labels explicatifs (metacognition #4 + progrès #8) ────────────
    if selected:
        labels = []
        total_duration = 0
        for s in selected:
            w = weights.get(s, 3)
            total_duration += w * 3
            if next_keys and s in next_keys:
                lbl = concept_label(s, norm.get(s, (0,None,0))[0], norm.get(s, (0,None,0))[1], today,
                                    tag=(next_niveau or "N+1") + " decouverte")
            elif s in norm:
                sc, ls, ds = norm[s]
                lbl = concept_label(s, sc, ls, today)
            else:
                lbl = concept_label(s, 0, None, today)
            labels.append(lbl)
        duration_hint = "~" + str(total_duration) + " min"
        concepts_display = " | ".join(labels)

        # Contexte score pour le LLM (mode TTT adaptatif)
        score_hints = []
        for s in selected:
            sc = norm.get(s, (0, None, 0))[0]
            if sc == 0:
                score_hints.append(s.replace("_", " ") + " → DECOUVERTE (score 0)")
            elif sc < 50:
                score_hints.append(s.replace("_", " ") + " → RENFORCEMENT (score " + str(sc) + ")")
            elif sc < 80:
                score_hints.append(s.replace("_", " ") + " → PRATIQUE (score " + str(sc) + ")")
            else:
                score_hints.append(s.replace("_", " ") + " → MAINTIEN (score " + str(sc) + ")")
        concept_modes = " | ".join(score_hints)

        # ── FOCUS CONCEPT : le système décide quel concept travailler à chaque tour ──
        # Tours 2-5 → concept 1 | Tour 5 = transition | Tours 6+ → concept 2
        TRANSITION_TOUR = 6
        if len(selected) >= 2:
            if n < TRANSITION_TOUR:
                focus_concept = selected[0].replace("_", " ")
                focus_mode = score_hints[0]
                if n == TRANSITION_TOUR - 1:
                    transition_instruction = (
                        ">>> C'est le DERNIER tour sur " + focus_concept + ". "
                        "Fais une micro-synthese (1 phrase : ce qu'on retient) "
                        "puis annonce : 'On passe a " + selected[1].replace("_", " ") + " !'"
                    )
                else:
                    transition_instruction = ""
            else:
                focus_concept = selected[1].replace("_", " ")
                focus_mode = score_hints[1]
                if n == 9:
                    transition_instruction = (
                        ">>> DERNIER TOUR. Fais une synthese globale de la session "
                        "(les 2 concepts, ce que l'eleve retient)."
                    )
                else:
                    transition_instruction = ""
        elif len(selected) == 1:
            focus_concept = selected[0].replace("_", " ")
            focus_mode = score_hints[0]
            transition_instruction = ""
        else:
            focus_concept = ""
            focus_mode = ""
            transition_instruction = ""
    else:
        concepts_display = "choisir librement depuis le curriculum"
        concept_modes = ""
        duration_hint = ""
        focus_concept = ""
        focus_mode = ""
        transition_instruction = ""

    # --- FRESH PROMOTION DETECTION ---
    # Detecte si l'eleve vient de reussir un examen cette session (sessions_since=0)
    fresh_promotion = False
    fresh_score = 0
    fresh_prev_niveau = ""
    if dernier_examen and isinstance(dernier_examen, dict):
        if dernier_examen.get('passed') and int(sessions_since) == 0 and not promotion_ready:
            fresh_promotion = True
            fresh_score = dernier_examen.get('score', 0)
            fresh_prev_niveau = dernier_examen.get('niveau', '?')

    promotion_msg = ""
    plan_prefix = ""

    # --- PRIORITE 0 : CELEBRATION POST-PROMOTION ---
    if fresh_promotion:
        plan_prefix = (
            ">>> INSTRUCTION PRIORITAIRE — FELICITATION PROMOTION <<<\n"
            "L'eleve vient de reussir l'examen " + fresh_prev_niveau + " → " + niveau + " (score : " + str(fresh_score) + "/100) !\n"
            "Ta reponse DOIT contenir dans cet ordre :\n"
            "1. Felicitation sincere et chaleureuse (1-2 phrases). Mentionne le score.\n"
            "2. Annonce que vous decouvrez maintenant le " + niveau + " ensemble.\n"
            "3. Plan de session normal avec les concepts selectionnes.\n"
            "INTERDIT : proposer un examen ou mentionner 'examen'. Il faut d'abord pratiquer le nouveau niveau.\n"
            ">>> FIN INSTRUCTION PRIORITAIRE <<<"
        )

    if promotion_ready and cooldown_met:
        nxt = next_niveau or "niveau suivant"
        promotion_msg = "PROMOTION DISPONIBLE"
        plan_prefix = (
            ">>> INSTRUCTION PRIORITAIRE — A SUIVRE AVANT TOUT <<<\n"
            "L'eleve maitrise " + str(int(pct_mastered)) + "% du " + niveau + ".\n"
            "Ta reponse DOIT commencer par cette phrase EXACTE (copie-la) :\n"
            "\"Bravo ! Tu maitrises " + str(int(pct_mastered)) + "% du " + niveau + " ! "
            "Tu veux tenter l'examen de passage vers le " + nxt + " ? "
            "Sinon on continue a s'entrainer.\"\n"
            "Puis affiche le plan normalement.\n"
            ">>> FIN INSTRUCTION PRIORITAIRE <<<"
        )
    elif promotion_ready and not cooldown_met:
        promotion_msg = "COOLDOWN ACTIF (" + cooldown_reason + ") — ne pas proposer l'examen mais l'eleve peut toujours le demander"
    elif approaching_promo:
        promotion_msg = "QUASI-PRET : " + str(int(pct_mastered)) + "% maitrise mais " + str(len(untested)) + " concept(s) jamais travaille(s). On les couvre d'abord."
    elif mastered_but_fresh and not promotion_ready:
        nb_fresh = len(mastered_but_fresh)
        promotion_msg = "CONSOLIDATION : " + str(nb_fresh) + " concept(s) ont un bon score mais doivent etre revus un autre jour pour etre valides."
    elif exploring_next and next_keys:
        promotion_msg = "L'eleve maitrise le " + niveau + ". Un concept " + (next_niveau or "N+1") + " est inclus en decouverte."

    # --- #5 COOLDOWN MODULE ECHOUE ---
    # Si l'eleve vient de rater un module (sessions_since=0, passed=False)
    # → guider vers consolidation AVANT de repasser
    if not plan_prefix and dernier_examen and isinstance(dernier_examen, dict):
        if not dernier_examen.get('passed') and int(sessions_since) == 0 and not fresh_promotion:
            score = dernier_examen.get('score', 0)
            to_review_list = dernier_examen.get('to_review', [])
            to_review_str = ", ".join(to_review_list) if to_review_list else "voir bilan precedent"
            plan_prefix = (
                ">>> INSTRUCTION PRIORITAIRE — MODULE ECHOUE <<<\n"
                "L'eleve vient d'echouer un module d'examen (score: " + str(score) + "/100, minimum 70).\n"
                "Concepts a consolider : " + to_review_str + "\n"
                "Ta reponse DOIT :\n"
                "1. Mentionner l'echec tres brievement et sans dramatiser (1 phrase).\n"
                "2. Proposer de consolider les concepts faibles AVANT de repasser le module.\n"
                "3. Afficher le plan avec ces concepts en priorite.\n"
                "INTERDIT : proposer de repasser l'examen maintenant.\n"
                ">>> FIN INSTRUCTION PRIORITAIRE <<<"
            )
            # Override selected_concepts avec les concepts faibles du module rate
            if to_review_list:
                labels = [c.replace("_", " ") + " [a consolider]" for c in to_review_list[:3]]
                concepts_display = " | ".join(labels)

    # --- #6 REVIEW MODE (demande manuelle revision lacunes) ---
    # Si l'eleve a demande [REVIEW_LACUNES] lors du tour precedent
    if str(review_mode or '').strip() == 'active' and not plan_prefix:
        review_selected = []
        for k, v in weak:
            if len(review_selected) < 4:
                review_selected.append(k)
        for k in untested:
            if len(review_selected) < 4 and k not in review_selected:
                review_selected.append(k)
        if review_selected:
            labels = [c.replace("_", " ") + " [lacune]" for c in review_selected]
            concepts_display = " | ".join(labels)
        else:
            # Rien de vraiment faible — prendre les plus bas scores
            all_sorted = sorted(scored_concepts.items(), key=lambda x: x[1])
            for k, v in all_sorted[:3]:
                review_selected.append(k)
            if review_selected:
                labels = [c.replace("_", " ") + " [a renforcer]" for c in review_selected]
                concepts_display = " | ".join(labels)
        plan_prefix = (
            ">>> MODE REVISION ACTIVE <<<\n"
            "L'eleve a demande a revoir ses lacunes.\n"
            "Ta reponse DOIT :\n"
            "1. Confirmer brievement le mode revision (1 phrase).\n"
            "2. Afficher le plan avec uniquement les concepts faibles/non testes listes.\n"
            "INTERDIT : proposer un examen.\n"
            ">>> FIN MODE REVISION <<<"
        )

    # --- SCORING RECOVERY MESSAGE ---
    if scoring_recovery and not plan_prefix:
        plan_prefix = (
            ">>> INSTRUCTION PRIORITAIRE <<<\n"
            "L'examen precedent a rencontre un probleme technique.\n"
            "Dis a l'eleve : \"Desole, il y a eu un souci technique avec ton dernier examen. "
            "Tu peux le retenter quand tu veux.\"\n"
            "Puis affiche le plan normalement.\n"
            ">>> FIN INSTRUCTION PRIORITAIRE <<<"
        )

    # --- ABSENCE-AWARE WELCOME (based on minutes_since_last, lowest priority) ---
    # Uses minutes_since_last from FastAPI (time since last message in conversation)
    mins = int(minutes_since_last or 0)

    if mins >= 60 and not plan_prefix:
        if mins >= 10080:  # 7+ days
            days = mins // 1440
            plan_prefix = (
                ">>> INSTRUCTION ACCUEIL — LONGUE ABSENCE <<<\n"
                "L'eleve revient apres " + str(days) + " jours d'absence.\n"
                "Ton accueil DOIT :\n"
                "1. Mentionner que ca fait longtemps (content de le revoir, sans culpabiliser).\n"
                "2. Proposer une revision en douceur des concepts les plus rouilles (ceux avec ⏰ dans le plan).\n"
                "3. Ton ton doit etre chaleureux et encourageant, comme retrouver un ami.\n"
                ">>> FIN INSTRUCTION ACCUEIL <<<"
            )
        elif mins >= 1440:  # 1-6 days
            days = mins // 1440
            plan_prefix = (
                ">>> INSTRUCTION ACCUEIL — QUELQUES JOURS <<<\n"
                "L'eleve revient apres " + str(days) + " jour(s).\n"
                "Mentionne brievement son retour (ex: 'Ca fait quelques jours !').\n"
                "Propose de revoir les points qui ont pu etre oublies.\n"
                "Enchaine sur le plan de session.\n"
                ">>> FIN INSTRUCTION ACCUEIL <<<"
            )
        elif mins >= 60:  # 1h-24h
            hours = mins // 60
            plan_prefix = (
                ">>> INSTRUCTION ACCUEIL — NOUVELLE SESSION <<<\n"
                "L'eleve revient apres " + str(hours) + "h d'absence.\n"
                "Accueille-le brievement ('On reprend !' ou similaire).\n"
                "Genere un plan de session frais base sur les concepts selectionnes.\n"
                ">>> FIN INSTRUCTION ACCUEIL <<<"
            )
        # < 60 min : continuation silencieuse, pas de plan_prefix

    exam_active = exam != 'off'

    # --- COMPUTE EXAM MODULES ---
    exam_modules_json = "[]"
    try:
        groups = json.loads(concept_groups_json or '{}')
    except:
        groups = {}

    if groups and weights:
        ratio_map = {'A1': 70, 'A2': 60, 'B1': 50, 'B2': 40, 'C1': 30, 'C2': 20}
        targeted_pct = ratio_map.get(niveau, 50)
        level_types_map = {
            'A1': 'FILL,CHOICE,PRODUCE',
            'A2': 'FILL,CHOICE,CORRECT,PRODUCE',
            'B1': 'FILL,CHOICE,CORRECT,TRANSFORM,PRODUCE',
            'B2': 'FILL,CHOICE,CORRECT,TRANSFORM,FORM,PRODUCE',
            'C1': 'FILL,CHOICE,CORRECT,TRANSFORM,FORM,PRODUCE',
            'C2': 'FILL,CHOICE,CORRECT,TRANSFORM,FORM,PRODUCE'
        }
        q_types = level_types_map.get(niveau, 'FILL,CHOICE,CORRECT,TRANSFORM,PRODUCE')

        modules = []
        for group_name, group_concepts in groups.items():
            total_q = sum(weights.get(c, 3) for c in group_concepts)
            concepts_with_weights = []
            for c in group_concepts:
                w = weights.get(c, 3)
                concepts_with_weights.append({"key": c, "weight": w})
            modules.append({
                "name": group_name,
                "concepts": concepts_with_weights,
                "total_questions": total_q,
                "targeted_pct": targeted_pct,
                "question_types": q_types
            })
        exam_modules_json = json.dumps(modules)

    # ── MOCK EXAM (Quiz) — piloté par le frontend via input ──
    mock_exam_input = str(mock_exam or '').strip()
    mock_exam_instruction = ''

    if mock_exam_input and not exam_active:
        # Format: "Q3/10:conditional_2:DECOUVERTE" or "start" or "bilan"
        if mock_exam_input == 'bilan':
            mock_exam_instruction = (
                ">>> QUIZ TERMINE — BILAN <<<\n"
                "Fais un bilan de ce quiz en 5-8 lignes :\n"
                "1. Score approximatif (X/10 environ basé sur ce que tu as vu)\n"
                "2. Pour chaque concept travaillé : ✅ (solide), ⚠️ (fragile), ou ❌ (a retravailler)\n"
                "3. Un conseil personnalisé en 1-2 phrases\n"
                "Sois encourageant mais honnête.\n"
                ">>> FIN BILAN <<<"
            )
        elif mock_exam_input.startswith('Q'):
            # Parse "Q3/10:conditional_2:DECOUVERTE"
            parts = mock_exam_input.split(':')
            q_part = parts[0] if len(parts) >= 1 else 'Q1/10'
            concept_part = parts[1].replace('_', ' ') if len(parts) >= 2 else ''
            mode_part = parts[2] if len(parts) >= 3 else 'DECOUVERTE'

            # Build a human-readable hint for the concept
            concept_hint_map = {
                'present_perfect_simple': 'have/has + past participle (I have visited)',
                'present_perfect_vs_past_simple': 'quand utiliser have done vs did',
                'present_perfect_continuous': 'have been + -ing (I have been working)',
                'past_perfect': 'had + past participle (I had finished)',
                'passive_voice': 'be + past participle (It was built)',
                'conditional_1': 'if + present → will (If it rains, I will stay)',
                'conditional_2': 'if + past → would (If I had money, I would travel)',
                'modal_deduction': 'must/might/can\'t be (She must be tired)',
                'reported_speech': 'He said that... / She told me that...',
                'indirect_questions': 'Could you tell me where...?',
                'phrasal_verbs': 'verbes a particule (look up, give in, turn off)',
                'gerund_vs_infinitive': 'enjoy doing vs want to do',
                'relative_clauses': 'who/which/that/where/whose',
                'connectors': 'although, however, despite, whereas',
                'used_to': 'used to + base (I used to live there)',
                'would_habitual': 'would + base pour habitudes passees',
                'adj_prepositions': 'good at, interested in, afraid of',
                'adverbs_degree': 'quite, rather, fairly, extremely',
                'so_such_that': 'so + adj / such + noun (so tired that...)',
                'both_either_neither': 'both...and / either...or / neither...nor',
            }
            concept_hint = concept_hint_map.get(parts[1] if len(parts) >= 2 else '', '')

            mock_exam_instruction = (
                ">>> MODE QUIZ — IGNORE TOUTES LES AUTRES INSTRUCTIONS CI-DESSOUS <<<\n"
                "Tu es en mode QUIZ. NE fais PAS de plan. NE presente PAS les concepts. IGNORE l'historique.\n\n"
                "" + q_part + "\n"
                "CONCEPT OBLIGATOIRE : " + concept_part + "\n"
                + ("AIDE : " + concept_hint + "\n" if concept_hint else "")
                + "Tu DOIS poser une question sur CE concept et AUCUN autre.\n"
                "Pose UNE question (traduction FR→EN, ou phrase a completer, ou correction d'erreur).\n"
                "Maximum 2 lignes.\n\n"
                "Si l'eleve a deja repondu a la question precedente :\n"
                "- Correct : ✅ + pourquoi en 1 ligne\n"
                "- Incorrect : ❌ sa reponse → ✅ la bonne + explication en 2 lignes max\n"
                ">>> FIN QUIZ <<<"
            )

    return {
        'is_first_turn': n == 1,
        'tour': n,
        'niveau': niveau,
        'selected_concepts': concepts_display,
        'concept_modes': concept_modes,
        'focus_concept': focus_concept if not exam_active and not mock_exam_instruction else '',
        'focus_mode': focus_mode if not exam_active and not mock_exam_instruction else '',
        'transition_instruction': transition_instruction if not exam_active and not mock_exam_instruction else '',
        'duration_hint': duration_hint,
        'promotion_ready': promotion_ready,
        'promotion_msg': promotion_msg,
        'plan_prefix': mock_exam_instruction if mock_exam_instruction else plan_prefix,
        'pct_mastered': int(pct_mastered),
        'exam_active': exam_active,
        'exam_modules_json': exam_modules_json,
        'exam_resume_needed': exam_resume_needed,
        'scoring_recovery': scoring_recovery
    }
"""

CODE_CHECK = r"""def main(nb: int, profil_present: bool, exam_mode: str) -> dict:
    n = int(nb or 0) + 1
    in_exam = str(exam_mode or 'off') != 'off'
    do_snap = n % 10 == 0 and bool(profil_present) and not in_exam
    return {"new_count": n, "do_snapshot": do_snap}
"""

CODE_EXAM_TRACK = r"""import json

def main(text: str, exam_question_num: int, exam_responses: str, query: str,
         exam_total_questions: int) -> dict:
    num = int(exam_question_num or 0)
    total = int(exam_total_questions or 20)

    try:
        responses = json.loads(exam_responses or '[]')
    except:
        responses = []

    # --- ABORT : eleve veut arreter ---
    if "[EXAM_ABORT]" in text:
        cleaned = text.replace("[EXAM_ABORT]", "").strip()
        return {
            "cleaned_text": cleaned, "new_exam_mode": "off",
            "new_question_num": 0, "new_responses": "[]",
            "exam_complete": False, "exam_aborted": True
        }

    # --- REPEAT : message parasite, ne pas incrementer ---
    if "[REPEAT_QUESTION]" in text:
        cleaned = text.replace("[REPEAT_QUESTION]", "").strip()
        return {
            "cleaned_text": cleaned, "new_exam_mode": "active",
            "new_question_num": num, "new_responses": json.dumps(responses),
            "exam_complete": False, "exam_aborted": False
        }

    # --- COMPLETE : derniere question repondue ---
    if "[EXAM_COMPLETE]" in text:
        cleaned = text.replace("[EXAM_COMPLETE]", "").strip()
        if num > 0 and query:
            responses.append({"q": num, "answer": query[:500]})
        return {
            "cleaned_text": cleaned, "new_exam_mode": "scoring",
            "new_question_num": num, "new_responses": json.dumps(responses),
            "exam_complete": True, "exam_aborted": False
        }

    # --- NORMAL : enregistrer reponse, incrementer ---
    if num == 0:
        new_num = 1
    else:
        if query:
            responses.append({"q": num, "answer": query[:500]})
        new_num = num + 1

    return {
        "cleaned_text": text, "new_exam_mode": "active",
        "new_question_num": new_num, "new_responses": json.dumps(responses),
        "exam_complete": False, "exam_aborted": False
    }
"""

CODE_EXAM_DETECT = r"""import json

def main(text: str, current_exam_mode: str, exam_modules_json: str) -> dict:
    # --- Detect EXAM_START ---
    marker = "[EXAM_START]"
    if marker in text:
        cleaned = text.replace(marker, "").strip()
        # Load modules and prepare first module
        modules = []
        try:
            modules = json.loads(exam_modules_json or '[]')
        except:
            modules = []

        if modules and len(modules) > 0:
            first = modules[0]
            module_name = first.get("name", "Module 1")
            total_q = first.get("total_questions", 20)
            concepts = first.get("concepts", [])
            concepts_display = ", ".join([c["key"] + " (x" + str(c["weight"]) + ")" for c in concepts])
        else:
            module_name = "Examen"
            total_q = 20
            concepts_display = ""

        return {
            "cleaned_text": cleaned, "new_exam_mode": "intro", "exam_triggered": True,
            "exam_module_index": 0, "exam_module_total": len(modules),
            "exam_module_name": module_name, "exam_total_questions": total_q,
            "exam_module_concepts": concepts_display, "exam_modules": exam_modules_json or "[]",
            "review_mode_value": ""
        }

    # --- Detect REVIEW_LACUNES (#6) ---
    review_marker = "[REVIEW_LACUNES]"
    if review_marker in text:
        cleaned = text.replace(review_marker, "").strip()
        return {
            "cleaned_text": cleaned, "new_exam_mode": current_exam_mode, "exam_triggered": False,
            "exam_module_index": 0, "exam_module_total": 0,
            "exam_module_name": "", "exam_total_questions": 0,
            "exam_module_concepts": "", "exam_modules": "[]",
            "review_mode_value": "active"
        }

    return {
        "cleaned_text": text, "new_exam_mode": current_exam_mode, "exam_triggered": False,
        "exam_module_index": 0, "exam_module_total": 0,
        "exam_module_name": "", "exam_total_questions": 0,
        "exam_module_concepts": "", "exam_modules": "[]",
        "review_mode_value": ""
    }
"""

CODE_EXAM_BILAN = r"""import json

def main(body: str, exam_text: str, exam_module_index: int, exam_module_total: int,
         exam_module_name: str, exam_modules: str) -> dict:
    try:
        result = json.loads(body or '{}')
    except:
        result = {}

    # --- Error handling : scoring n8n failed ---
    if not result or (not result.get('concept_scores') and not result.get('total_score')):
        error_text = (exam_text or "") + (
            "\n\n--- ERREUR TECHNIQUE ---\n"
            "La correction a rencontre un probleme. Votre progression est sauvegardee.\n"
            "Vous pourrez retenter l'examen lors de votre prochaine session.\n"
            "Toutes mes excuses pour ce desagrement."
        )
        return {
            "bilan_text": error_text,
            "module_passed": False, "has_next_module": False, "all_modules_passed": False,
            "reset_exam_mode": "off", "reset_question_num": 0, "reset_responses": "[]",
            "reset_module_index": 0, "reset_module_name": "",
            "reset_total_questions": 0, "reset_module_concepts": ""
        }

    module_passed = result.get('passed', False)
    score = result.get('total_score', 0)
    niveau = result.get('niveau', '?')
    commentaire = result.get('commentaire', '')
    concept_scores = result.get('concept_scores', {})

    idx = int(exam_module_index or 0)
    total_modules = int(exam_module_total or 1)
    mod_name = str(exam_module_name or 'Module')

    try:
        modules = json.loads(exam_modules or '[]')
    except:
        modules = []

    # --- Build module result line ---
    next_idx = idx + 1
    all_passed = module_passed and next_idx >= total_modules
    next_level = {'A1':'A2','A2':'B1','B1':'B2','B2':'C1','C1':'C2'}.get(niveau, '?')

    if module_passed:
        bilan = "\n\n✅ Module " + str(idx + 1) + "/" + str(total_modules) + " — " + mod_name + " : " + str(score) + "/100\n"
    else:
        bilan = "\n\n❌ Module " + str(idx + 1) + "/" + str(total_modules) + " — " + mod_name + " : " + str(score) + "/100 (minimum 70)\n"

    # --- Detail per concept avec icones ---
    if concept_scores:
        bilan += "\n"
        to_review = []
        for ckey, cdata in concept_scores.items():
            label = ckey.replace("_", " ")
            if isinstance(cdata, dict):
                cs = int(cdata.get("score", 0))
                ct = int(cdata.get("total", 1))
                pct = cs / ct if ct > 0 else 0
                if pct >= 0.8:
                    icon = "✅"
                elif pct >= 0.6:
                    icon = "⚠️"
                else:
                    icon = "❌"
                    to_review.append(label)
                bilan += icon + " " + label + " : " + str(cs) + "/" + str(ct) + "\n"
            else:
                bilan += "• " + label + " : " + str(cdata) + "\n"
    else:
        to_review = []

    if commentaire:
        bilan += "\n" + commentaire + "\n"

    # --- Check if more modules remain ---
    has_next = module_passed and next_idx < total_modules

    if has_next:
        next_mod = modules[next_idx] if next_idx < len(modules) else None
        if next_mod:
            next_name = next_mod.get("name", "Module " + str(next_idx + 1))
            next_total = next_mod.get("total_questions", 20)
            next_concepts = next_mod.get("concepts", [])
            next_concepts_display = ", ".join([c["key"] + " (x" + str(c["weight"]) + ")" for c in next_concepts])
            bilan += "\n➡️  Module suivant : " + next_name + " (" + str(next_total) + " questions)\n"
            bilan += "Prêt(e) ? Répondez 'oui' pour continuer.\n"
        else:
            next_name = ""
            next_total = 0
            next_concepts_display = ""
            has_next = False
    else:
        next_name = ""
        next_total = 0
        next_concepts_display = ""

    if all_passed:
        bilan += "\n🎉 TOUS LES MODULES RÉUSSIS — Vous passez en " + next_level + " !\n"

    if not module_passed:
        if to_review:
            bilan += "\nÀ retravailler : " + ", ".join(to_review) + "\n"
        bilan += "Ce module est à repasser. On va consolider ça ensemble !\n"

    full_text = (exam_text or "Examen termine.") + bilan

    # --- Prepare values for var_assigner_exam_reset ---
    # If next module: keep exam alive with new module info
    # If no next: full reset
    if has_next:
        reset_exam_mode = "intro"
        reset_question_num = 0
        reset_responses = "[]"
        reset_module_index = next_idx
        reset_module_name = next_name
        reset_total_questions = next_total
        reset_module_concepts = next_concepts_display
    else:
        reset_exam_mode = "off"
        reset_question_num = 0
        reset_responses = "[]"
        reset_module_index = 0
        reset_module_name = ""
        reset_total_questions = 0
        reset_module_concepts = ""

    return {
        "bilan_text": full_text,
        "module_passed": module_passed,
        "has_next_module": has_next,
        "all_modules_passed": module_passed and next_idx >= total_modules,
        "reset_exam_mode": reset_exam_mode,
        "reset_question_num": reset_question_num,
        "reset_responses": reset_responses,
        "reset_module_index": reset_module_index,
        "reset_module_name": reset_module_name,
        "reset_total_questions": reset_total_questions,
        "reset_module_concepts": reset_module_concepts
    }
"""

CODE_EXAM_PERSIST = r"""import json

def main(new_exam_mode: str, new_question_num: int, new_responses: str,
         module_index: int, module_total: int, module_name: str,
         module_concepts: str, total_questions: int, modules_json: str,
         username: str) -> dict:
    mode = str(new_exam_mode or 'off')
    if mode in ('off', 'scoring'):
        return {"persist_body": json.dumps({"username": str(username), "domaine": "anglais", "clear": True})}
    state = {
        "mode": mode,
        "question_num": int(new_question_num or 0),
        "responses": new_responses or "[]",
        "module_index": int(module_index or 0),
        "module_total": int(module_total or 1),
        "module_name": str(module_name or ""),
        "module_concepts": str(module_concepts or ""),
        "total_questions": int(total_questions or 20),
        "modules_json": modules_json or "[]"
    }
    return {"persist_body": json.dumps({"username": str(username), "domaine": "anglais", "exam_state": state})}
"""

# ============================================================
# LLM PROMPTS
# ============================================================

PROMPT_PLAN = (
    "{{#code_turn_check.plan_prefix#}}\n\n"
    "=== SI LE TEXTE CI-DESSUS CONTIENT 'MODE QUIZ' ===\n"
    "→ Suis UNIQUEMENT les instructions du MODE QUIZ. Ignore TOUT ce qui suit.\n"
    "=== SINON : PLAN DE SESSION ===\n\n"
    "Tu es Teacher, prof d'anglais. Maximum 5 lignes — regle absolue.\n\n"
    "PROFIL :\n{{#code_profil_check.profil_text#}}\n\n"
    "CONCEPTS DE SESSION : {{#code_turn_check.selected_concepts#}}\n"
    "DUREE ESTIMEE : {{#code_turn_check.duration_hint#}}\n\n"
    "STRUCTURE DE TA REPONSE :\n"
    "1. Accueil chaleureux (1 ligne, detail du profil)\n"
    "2. Plan avec raisons :\n"
    "   📋 Session — {{#code_turn_check.niveau#}} • {{#code_turn_check.duration_hint#}}\n"
    "   • [concept 1] — [traduis la raison du label : 🆕=nouveau, ⏰=a revoir, ⚡=point faible, ✅=consolidation]\n"
    "   • [concept 2] — [idem]\n"
    '   Si un concept est marque [decouverte] : "on teste un truc nouveau du niveau suivant"\n'
    '3. "Tu veux commencer par lequel ?"\n\n'
    "INTERDICTIONS ABSOLUES :\n"
    "- NE JAMAIS inclure [EXAM_START]\n"
    "- NE JAMAIS demarrer un examen sauf si INSTRUCTION PRIORITAIRE le demande\n"
    "- Tu n'enseignes rien ici. Tu presentes juste le plan."
)

PROMPT_SESSION = (
    "{{#code_turn_check.plan_prefix#}}\n\n"
    "=== SI LE TEXTE CI-DESSUS CONTIENT 'MODE QUIZ' ===\n"
    "→ Suis UNIQUEMENT les instructions du MODE QUIZ. Ignore TOUT ce qui suit.\n"
    "=== SINON : SESSION NORMALE ===\n\n"
    "Tu es Teacher, prof d'anglais. Bienveillant, direct, un peu d'humour.\n\n"
    "STATUT EXAMEN : {{#code_turn_check.promotion_msg#}}\n\n"
    "=== DETECTION EXAMEN (PRIORITAIRE) ===\n"
    'Si l\'eleve demande explicitement l\'examen (ex: "examen", "je veux l\'examen", "exam", "je suis pret") :\n'
    "  → Si STATUT EXAMEN contient 'PROMOTION DISPONIBLE' :\n"
    '    Reponds UNIQUEMENT : "Parfait, on passe en mode examen !"\n'
    "    Ajoute [EXAM_START] sur une ligne separee EN DESSOUS. Rien d'autre.\n"
    "  → Si STATUT EXAMEN ne contient PAS 'PROMOTION DISPONIBLE' :\n"
    "    REFUSE l'examen. Explique en 1-2 phrases qu'il faut d'abord couvrir davantage de concepts du niveau.\n"
    "    Redirige vers les concepts selectionnes. N'ajoute JAMAIS [EXAM_START].\n"
    "Ne mets JAMAIS [EXAM_START] si l'eleve n'a PAS demande explicitement l'examen.\n"
    "Ne mets JAMAIS [EXAM_START] si STATUT EXAMEN ne contient pas 'PROMOTION DISPONIBLE'.\n"
    "=== FIN DETECTION EXAMEN ===\n\n"
    "=== DETECTION REVISION LACUNES ===\n"
    'Si l\'eleve demande explicitement a revoir ses lacunes / retravailler ses points faibles / '
    '"mode revision" / "voir mes lacunes" / "revoir mes erreurs" :\n'
    '→ Reponds UNIQUEMENT : "Mode revision active ! On va cibler tes points faibles."\n'
    "→ Ajoute [REVIEW_LACUNES] sur une ligne separee EN DESSOUS. Rien d'autre.\n"
    "Ne mets JAMAIS [REVIEW_LACUNES] si l'eleve n'a PAS demande explicitement la revision.\n"
    "=== FIN DETECTION REVISION ===\n\n"
    "REGLES ABSOLUES — si tu en violes une, ta reponse est ratee :\n"
    "- Maximum 5 lignes par reponse. UNIQUEMENT pour les mini-lecons : 8 lignes max.\n"
    "- UNE seule question par message, jamais deux\n"
    "- Tu attends TOUJOURS la reponse avant d'avancer\n"
    "- Tu ne donnes JAMAIS la reponse a ta propre question\n"
    "- Ton naturel : pas de titres ##, pas de tableaux, pas de listes a puces sauf si indispensable\n"
    "- Tu tutoies\n\n"
    "PROFIL :\n{{#code_profil_check.profil_text#}}\n{{#conversation.session_snapshot#}}\n"
    "Tour de conversation : {{#code_turn_check.tour#}}\n\n"
    "CONCEPTS DE CETTE SESSION (choisis par le systeme) :\n"
    "{{#code_turn_check.selected_concepts#}}\n\n"
    ">>> CONCEPT ACTIF MAINTENANT : {{#code_turn_check.focus_concept#}}\n"
    ">>> MODE : {{#code_turn_check.focus_mode#}}\n"
    "{{#code_turn_check.transition_instruction#}}\n\n"
    "REGLE CRITIQUE : tu travailles UNIQUEMENT sur le CONCEPT ACTIF ci-dessus.\n"
    "Ne passe JAMAIS au concept suivant de toi-meme — le systeme te dira quand changer.\n"
    "Ne propose JAMAIS un concept d'un niveau superieur au niveau de l'eleve.\n\n"
    "=== APPROCHE TTT (Test → Teach → Test) ===\n\n"
    "TOUR 2 : l'eleve vient de voir le plan.\n"
    '  → Annonce : "Je pars sur [CONCEPT ACTIF] !"\n'
    "  → Lance le premier DEFI selon le MODE ci-dessus.\n\n"
    "TOURS 3+ : adapte ton comportement au MODE du concept actif :\n\n"
    "--- MODE DECOUVERTE (score 0) ---\n"
    "Le concept est nouveau. L'eleve ne l'a jamais vu.\n"
    "Etape 1 : Pose un DEFI CONTEXTUEL sans expliquer la regle.\n"
    '  Ex : "Comment tu dirais \'J\'habite ici depuis 3 ans\' en anglais ?"\n'
    "  PAS de regle avant. On teste ce que l'eleve sait naturellement.\n"
    "Etape 2a : Si correct → Bien joue ! Pose un defi plus dur, meme concept.\n"
    "Etape 2b : Si incorrect → NE CORRIGE PAS. Reformule le defi autrement.\n"
    '  "Essaie autrement : \'Elle travaille ici depuis 2020\'"\n'
    "Etape 3 : Si 2e echec → MINI-LECON (max 150 mots) :\n"
    "  1. Ce que l'eleve a dit → ce qu'il faut dire\n"
    "  2. POURQUOI (la logique, pas juste la formule)\n"
    "  3. Un CONTRASTE (quand ca marche vs quand ca marche pas)\n"
    "  4. Un exemple du quotidien\n"
    "  Puis re-teste le meme point sous un autre angle.\n\n"
    "--- MODE RENFORCEMENT (score 1-49) ---\n"
    "L'eleve a deja vu le concept mais ne le maitrise pas.\n"
    "Etape 1 : Defi direct (l'eleve connait le concept).\n"
    "Etape 2a : Si correct → Encourage + variante plus dure.\n"
    "Etape 2b : Si incorrect → CORRECTION CIBLEE (3-4 lignes) :\n"
    "  ❌ ce qu'il a dit → ✅ ce qu'il faut\n"
    "  💡 POURQUOI en 1-2 phrases (la logique)\n"
    "  Puis redemande (meme point, angle different).\n\n"
    "--- MODE PRATIQUE (score 50-79) ---\n"
    "Defi varie (contextes differents de la derniere fois).\n"
    "Si correct → encourage + question suivante.\n"
    "Si incorrect → ❌ → ✅ + rappel rapide en 1 ligne. Redemande.\n\n"
    "--- MODE MAINTIEN (score 80+) ---\n"
    "Drill rapide de revision. Defi direct, contexte varie.\n"
    "Feedback court (1 ligne).\n\n"
    "=== FIN APPROCHE TTT ===\n\n"
    "VARIETE DE CONTEXTES :\n"
    "Alterne : sport, technologie, voyage, famille, travail, culture, environnement, cuisine, cinema.\n"
    "Ne repete jamais le meme domaine deux questions de suite."
)

PROMPT_ONBOARDING = (
    "Tu es Teacher, prof d'anglais. Maximum 100 mots. UNE question a la fois. Tu tutoies.\n"
    "LANGUE : Tu communiques EN FRANCAIS pendant toute la Phase 1. Tu passes a l'anglais UNIQUEMENT pour les questions du diagnostic en Phase 2.\n\n"
    "Cet eleve est nouveau, tu ne sais rien de lui. Tu vas faire 2 phases dans l'ordre.\n\n"
    "=== PHASE 1 — PERSONNALITE (tours 1 a 4) ===\n"
    "Pose ces questions naturellement, UNE par message :\n"
    "1. Comment tu t'appelles et pourquoi l'anglais ? (travail / voyage / culture / examen)\n"
    "2. Tu preferes etre corrige immediatement ou doucement ? Humour ou serieux ?\n"
    "3. Centres d'interet ?\n"
    "4. Comment tu veux qu'on avance ? Deux options :\n"
    "   - Mode structure : on travaille ton niveau a fond, et quand t'es pret je te propose un examen de validation pour monter au niveau suivant\n"
    "   - Mode libre : on progresse naturellement, j'introduis des choses plus avancees au fur et a mesure sans blocage\n"
    "   Presente les deux options clairement et demande son choix.\n\n"
    "Quand tu as les 4 reponses → annonce la phase 2 ET pose IMMEDIATEMENT la premiere question diagnostic dans le MEME message :\n"
    '"Maintenant je vais evaluer ton niveau CECRL avec quelques questions en anglais. Reponds naturellement, pas de stress !" puis enchaine directement avec la premiere question en anglais (palier A2-B1). Ne fais JAMAIS un message d\'annonce sans question.\n\n'
    "=== PHASE 2 — DIAGNOSTIC (tours 5 a 10+) ===\n"
    "Pose des questions EN ANGLAIS, de difficulte croissante. UNE par message, attends la reponse.\n\n"
    'Palier A1-A2 : "Tell me about yourself" / "What do you like to do?"\n'
    'Palier A2-B1 : "What did you do last weekend?" / "Describe your best friend"\n'
    'Palier B1    : "What would you do if you won the lottery?"\n'
    'Palier B1-B2 : "Tell me about a difficult decision you had to make"\n'
    'Palier B2    : "What are the pros and cons of remote work?"\n'
    'Palier B2-C1 : "How would the world be different if internet hadn\'t been invented?"\n'
    'Palier C1    : "Some argue that AI will replace teachers. Do you agree?"\n'
    'Palier C1-C2 : "To what extent does language shape thought?"\n\n'
    "REGLES DU DIAGNOSTIC :\n"
    "- Commence au palier A2-B1\n"
    "- Si l'eleve repond bien → monte d'un palier\n"
    "- Si l'eleve galere (erreurs frequentes, phrases courtes, melange francais) → STOP, tu as trouve le plafond\n"
    "- Ne corrige PAS les erreurs pendant le diagnostic (note-les mentalement)\n"
    "- Pose au MINIMUM 5 questions de niveaux differents\n"
    "- Si l'eleve divague ou pose des questions → recadre poliment et repose ta question\n\n"
    "QUAND TU AS ASSEZ DE DONNEES (minimum 5 questions posees + plafond identifie) :\n"
    'Dis : "Merci pour tes reponses ! Envoie-moi \'ok\' pour decouvrir ton bilan de niveau."\n'
    "Et ajoute le marqueur [EVAL_READY] A LA FIN de ton message (sur une ligne separee).\n\n"
    "NE JAMAIS mettre [EVAL_READY] avant d'avoir pose au moins 4 questions en anglais."
)

PROMPT_EXAM = (
    "Tu es un examinateur CECRL. Ton neutre, professionnel. Pas de blagues, pas d'emojis. Tu vouvoies.\n\n"
    "╔══════════════════════════════════════════════════════════╗\n"
    "║  REGLES D'EXAMEN — A RESPECTER SANS AUCUNE EXCEPTION    ║\n"
    "╠══════════════════════════════════════════════════════════╣\n"
    "║  1. UNE SEULE question par message. PAS DEUX. PAS PLUS.  ║\n"
    "║  2. JAMAIS corriger une reponse. Meme totalement fausse. ║\n"
    "║     Meme evidente. Meme catastrophique. JAMAIS.          ║\n"
    "║  3. JAMAIS expliquer une regle. JAMAIS donner d'indice.  ║\n"
    "║  4. JAMAIS valider ou invalider une reponse.             ║\n"
    "║     Poser la question suivante. C'est tout.              ║\n"
    "╚══════════════════════════════════════════════════════════╝\n\n"
    "NIVEAU CIBLE : {{#conversation.exam_niveau_from#}} -> {{#conversation.exam_niveau_to#}}\n"
    "MODULE EN COURS : {{#conversation.exam_module_name#}}\n"
    "CONCEPTS ET POIDS DU MODULE :\n{{#conversation.exam_module_concepts#}}\n"
    "NOMBRE TOTAL DE QUESTIONS CE MODULE : {{#conversation.exam_total_questions#}}\n"
    "Tour examen : {{#conversation.exam_question_num#}}\n\n"
    "=== PRIORITE 1 : MESSAGE PARASITE — verifier EN PREMIER ===\n"
    "Si l'historique de conversation contient des echanges ET que le message de l'eleve\n"
    "N'EST PAS une tentative de reponse a la question en cours :\n"
    "(exemples : 'lol', 'ok', 'attends', 'c'est quoi...?', 'next', emojis, blagues, hors-sujet)\n"
    "→ Repondez avec UN SEUL mot ou courte phrase (max 10 mots), reposez la MEME question mot pour mot.\n"
    "→ Ajoutez [REPEAT_QUESTION] sur une ligne separee a la fin.\n"
    "→ NE PAS avancer a la question suivante. NE PAS expliquer le concept.\n\n"
    "=== PRIORITE 2 : REPRISE APRES RECONNEXION ===\n"
    "UNIQUEMENT si : c'est le PREMIER MESSAGE de cette conversation (pas d'historique)\n"
    "ET Tour examen > 0 (l'eleve avait deja commence ce module).\n"
    "→ L'eleve reprend un examen interrompu lors d'une session precedente.\n"
    "→ Dites : 'Reprise — Module : [nom du module], Question [Tour examen+1]/[total].'\n"
    "→ Posez directement la question suivante. Pas de re-introduction.\n\n"
    "=== PRIORITE 3 : PREMIERE QUESTION (Tour examen = 0) ===\n"
    "SI Tour examen = 0 → vous etes OBLIGATOIREMENT a la Question 1.\n"
    "PEU IMPORTE ce que contient l'historique de conversation.\n"
    "L'historique peut contenir un examen precedent abandonne — IGNOREZ-LE entierement.\n\n"
    "VOTRE REPONSE DOIT COMMENCER PAR CES DEUX LIGNES — RECOPIEZ-LES MOT POUR MOT, SANS RIEN CHANGER :\n"
    "Module : {{#conversation.exam_module_name#}} — Examen {{#conversation.exam_niveau_from#}} vers {{#conversation.exam_niveau_to#}}\n"
    "{{#conversation.exam_total_questions#}} questions — je ne corrige pas pendant l'examen.\n\n"
    "PUIS posez immediatement :\n"
    "Question 1/{{#conversation.exam_total_questions#}} — [concept]\n[TYPE]\n[La question]\n\n"
    "=== PRIORITE 4 : REPONSE NORMALE (apres une reponse de l'eleve) ===\n"
    "Que la reponse soit CORRECTE, INCORRECTE, PARTIELLE, ou INCOMPREHENSIBLE :\n"
    "→ Vous posez UNIQUEMENT la question suivante. C'est tout.\n"
    "→ Format EXACT et OBLIGATOIRE :\n"
    "   Question [N]/{{#conversation.exam_total_questions#}} — [concept]\n"
    "   [TYPE]\n"
    "   [La question]\n"
    "→ RIEN avant. RIEN apres. PAS de ❌. PAS de ✅. PAS de 💡. PAS de 'Noted'.\n"
    "→ Exemple : l'eleve repond 'She runned' (faux) → vous ecrivez JUSTE :\n"
    "   'Question 5/22 — phrasal_verbs\nFILL\nComplete: She _____ (give) up smoking.'\n"
    "→ Si vous ajoutez UNE correction ou UNE explication, l'examen est invalide.\n\n"
    "=== ABANDON ===\n"
    "Si l'eleve dit j'arrete, annuler, stop, abandon, I quit, je veux arreter :\n"
    "Repondez : Examen annule. Vous pourrez le reprendre quand vous le souhaitez.\n"
    "Ajoutez [EXAM_ABORT] sur une ligne separee.\n\n"
    "=== DERNIERE QUESTION REPONDUE (question {{#conversation.exam_total_questions#}}) ===\n"
    "Repondez : Merci, ce module est termine. Correction en cours, cela prend quelques secondes...\n"
    "Ajoutez [EXAM_COMPLETE] sur une ligne separee.\n\n"
    "=== TYPES DE QUESTIONS (6 TYPES) ===\n"
    "Tu DOIS varier les types selon les poids ci-dessus :\n"
    "- FILL : Completez le trou (ex: 'I _____ (be) here since Monday.')\n"
    "- CORRECT : Corrigez l'erreur dans cette phrase (ex: 'If I would know...')\n"
    "- TRANSFORM : Reformulez avec le mot-cle impose, meme sens (inspire Cambridge Key Word Transformation)\n"
    "- CHOICE : QCM contextualise 3-4 options (ex: She _____ A) make B) do C) take — a decision)\n"
    "- FORM : Formez le mot correct a partir de la racine (ex: The _____ (RELY) of this system)\n"
    "- PRODUCE : Production libre guidee (ex: 'What would you do if...?' repondez en 2-3 phrases)\n\n"
    "=== DISTRIBUTION DES QUESTIONS ===\n"
    "Pour chaque concept, le POIDS indique le nombre de questions a lui consacrer.\n"
    "RATIO PRODUCE obligatoire selon le niveau {{#code_turn_check.niveau#}} :\n"
    "  A1-A2 : 20% PRODUCE minimum\n"
    "  B1    : 40% PRODUCE minimum — ex: concept poids 5 = 2 FILL/CORRECT + 2 PRODUCE + 1 TRANSFORM\n"
    "  B2    : 50% PRODUCE minimum — ex: concept poids 4 = 1 FILL + 1 CORRECT + 2 PRODUCE\n"
    "  C1-C2 : 60% PRODUCE minimum — ex: concept poids 3 = 1 FILL + 2 PRODUCE\n"
    "PRODUCE = production libre guidee, 2-3 phrases completes. Ne pas accepter un mot seul.\n"
    "Progression au sein d'un concept : reconnaissance (FILL/CHOICE) → application (CORRECT/TRANSFORM) → production (PRODUCE)\n\n"
    "VARIETE CONTEXTES : alterne les domaines (sport, tech, voyage, travail, famille, culture).\n"
    "Ne jamais utiliser le meme contexte deux questions de suite."
)


# ============================================================
# PATCH FUNCTION
# ============================================================

def patch_graph(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    existing_ids = {n["id"] for n in nodes}

    for node in nodes:
        data = node.get("data", {})
        nid = node["id"]

        # --- Start node: add minutes_since_last input ---
        if data.get("type") == "start":
            data["variables"] = [
                {
                    "type": "text-input",
                    "variable": "minutes_since_last",
                    "label": "minutes_since_last",
                    "required": False,
                    "max_length": 10,
                    "default": "0"
                },
                {
                    "type": "text-input",
                    "variable": "mock_exam",
                    "label": "mock_exam",
                    "required": False,
                    "max_length": 200,
                    "default": ""
                },
                {
                    "type": "text-input",
                    "variable": "mode_override",
                    "label": "mode_override",
                    "required": False,
                    "max_length": 20,
                    "default": ""
                }
            ]
            print("  Patched: start node (3 inputs: minutes_since_last, mock_exam, mode_override)")

        # --- Code nodes ---
        if nid == "code_profil_check":
            data["code"] = CODE_PROFIL_CHECK
            data["outputs"] = {
                "profil_present": {"type": "boolean", "children": None},
                "profil_text": {"type": "string", "children": None},
                "concept_keys_json": {"type": "string", "children": None},
                "scores_json": {"type": "string", "children": None},
                "mode_apprentissage": {"type": "string", "children": None},
                "next_concept_keys_json": {"type": "string", "children": None},
                "next_niveau": {"type": "string", "children": None},
                "examen_en_cours_json": {"type": "string", "children": None},
                "dernier_examen_json": {"type": "string", "children": None},
                "nb_examens_niveau": {"type": "number", "children": None},
                "sessions_depuis_examen": {"type": "number", "children": None},
                "concept_weights_json": {"type": "string", "children": None},
                "concept_groups_json": {"type": "string", "children": None},
                "exam_resume_active": {"type": "boolean", "children": None},
                "exam_resume_mode": {"type": "string", "children": None},
                "exam_resume_question_num": {"type": "number", "children": None},
                "exam_resume_responses": {"type": "string", "children": None},
                "exam_resume_module_index": {"type": "number", "children": None},
                "exam_resume_module_total": {"type": "number", "children": None},
                "exam_resume_module_name": {"type": "string", "children": None},
                "exam_resume_module_concepts": {"type": "string", "children": None},
                "exam_resume_total_questions": {"type": "number", "children": None},
                "exam_resume_modules_json": {"type": "string", "children": None},
                "exam_scoring_recovered": {"type": "boolean", "children": None},
                "derniere_session": {"type": "string", "children": None}
            }
            print("  Patched: code_profil_check")

        if nid == "code_turn_check":
            data["code"] = CODE_TURN_CHECK
            data["variables"] = [
                {"variable": "dialogue_count", "value_selector": ["sys", "dialogue_count"]},
                {"variable": "profil_text", "value_selector": ["code_profil_check", "profil_text"]},
                {"variable": "concept_keys_json", "value_selector": ["code_profil_check", "concept_keys_json"]},
                {"variable": "scores_json", "value_selector": ["code_profil_check", "scores_json"]},
                {"variable": "mode_apprentissage", "value_selector": ["code_profil_check", "mode_apprentissage"]},
                {"variable": "next_concept_keys_json", "value_selector": ["code_profil_check", "next_concept_keys_json"]},
                {"variable": "next_niveau", "value_selector": ["code_profil_check", "next_niveau"]},
                {"variable": "exam_mode", "value_selector": ["conversation", "exam_mode"]},
                {"variable": "dernier_examen_json", "value_selector": ["code_profil_check", "dernier_examen_json"]},
                {"variable": "sessions_depuis_examen", "value_selector": ["code_profil_check", "sessions_depuis_examen"]},
                {"variable": "concept_weights_json", "value_selector": ["code_profil_check", "concept_weights_json"]},
                {"variable": "concept_groups_json", "value_selector": ["code_profil_check", "concept_groups_json"]},
                {"variable": "examen_en_cours_json", "value_selector": ["code_profil_check", "examen_en_cours_json"]},
                {"variable": "exam_scoring_recovered", "value_selector": ["code_profil_check", "exam_scoring_recovered"]},
                {"variable": "review_mode", "value_selector": ["conversation", "review_mode"]},
                {"variable": "derniere_session", "value_selector": ["code_profil_check", "derniere_session"]},
                {"variable": "minutes_since_last", "value_selector": ["1775343637677", "minutes_since_last"]},
                {"variable": "mock_exam", "value_selector": ["1775343637677", "mock_exam"]},
                {"variable": "mode_override", "value_selector": ["1775343637677", "mode_override"]}
            ]
            data["outputs"] = {
                "is_first_turn": {"type": "boolean", "children": None},
                "tour": {"type": "number", "children": None},
                "niveau": {"type": "string", "children": None},
                "selected_concepts": {"type": "string", "children": None},
                "concept_modes": {"type": "string", "children": None},
                "focus_concept": {"type": "string", "children": None},
                "focus_mode": {"type": "string", "children": None},
                "transition_instruction": {"type": "string", "children": None},
                "promotion_ready": {"type": "boolean", "children": None},
                "promotion_msg": {"type": "string", "children": None},
                "plan_prefix": {"type": "string", "children": None},
                "duration_hint": {"type": "string", "children": None},
                "pct_mastered": {"type": "number", "children": None},
                "exam_active": {"type": "boolean", "children": None},
                "exam_modules_json": {"type": "string", "children": None},
                "exam_resume_needed": {"type": "boolean", "children": None},
                "scoring_recovery": {"type": "boolean", "children": None}
            }
            print("  Patched: code_turn_check")

        if nid == "code_check":
            data["code"] = CODE_CHECK
            data["variables"] = [
                {"variable": "nb", "value_selector": ["conversation", "nb_interactions"]},
                {"variable": "profil_present", "value_selector": ["code_profil_check", "profil_present"]},
                {"variable": "exam_mode", "value_selector": ["conversation", "exam_mode"]}
            ]
            print("  Patched: code_check")

        if nid == "code_exam_track":
            data["code"] = CODE_EXAM_TRACK
            data["variables"] = [
                {"variable": "text", "value_selector": ["llm_exam", "text"]},
                {"variable": "exam_question_num", "value_selector": ["conversation", "exam_question_num"]},
                {"variable": "exam_responses", "value_selector": ["conversation", "exam_responses"]},
                {"variable": "query", "value_selector": ["sys", "query"]},
                {"variable": "exam_total_questions", "value_selector": ["conversation", "exam_total_questions"]}
            ]
            data["outputs"] = {
                "cleaned_text": {"type": "string", "children": None},
                "new_exam_mode": {"type": "string", "children": None},
                "new_question_num": {"type": "number", "children": None},
                "new_responses": {"type": "string", "children": None},
                "exam_complete": {"type": "boolean", "children": None},
                "exam_aborted": {"type": "boolean", "children": None}
            }
            print("  Patched: code_exam_track")

        if nid == "code_exam_detect":
            data["code"] = CODE_EXAM_DETECT
            data["variables"] = [
                {"variable": "text", "value_selector": ["llm_session", "text"]},
                {"variable": "current_exam_mode", "value_selector": ["conversation", "exam_mode"]},
                {"variable": "exam_modules_json", "value_selector": ["code_turn_check", "exam_modules_json"]}
            ]
            data["outputs"] = {
                "cleaned_text": {"type": "string", "children": None},
                "new_exam_mode": {"type": "string", "children": None},
                "exam_triggered": {"type": "boolean", "children": None},
                "exam_module_index": {"type": "number", "children": None},
                "exam_module_total": {"type": "number", "children": None},
                "exam_module_name": {"type": "string", "children": None},
                "exam_total_questions": {"type": "number", "children": None},
                "exam_module_concepts": {"type": "string", "children": None},
                "exam_modules": {"type": "string", "children": None},
                "review_mode_value": {"type": "string", "children": None}
            }
            print("  Patched: code_exam_detect")

        if nid == "code_exam_bilan":
            data["code"] = CODE_EXAM_BILAN
            data["variables"] = [
                {"variable": "body", "value_selector": ["http_exam_scoring", "body"]},
                {"variable": "exam_text", "value_selector": ["code_exam_track", "cleaned_text"]},
                {"variable": "exam_module_index", "value_selector": ["conversation", "exam_module_index"]},
                {"variable": "exam_module_total", "value_selector": ["conversation", "exam_module_total"]},
                {"variable": "exam_module_name", "value_selector": ["conversation", "exam_module_name"]},
                {"variable": "exam_modules", "value_selector": ["conversation", "exam_modules"]}
            ]
            data["outputs"] = {
                "bilan_text": {"type": "string", "children": None},
                "module_passed": {"type": "boolean", "children": None},
                "has_next_module": {"type": "boolean", "children": None},
                "all_modules_passed": {"type": "boolean", "children": None},
                "reset_exam_mode": {"type": "string", "children": None},
                "reset_question_num": {"type": "number", "children": None},
                "reset_responses": {"type": "string", "children": None},
                "reset_module_index": {"type": "number", "children": None},
                "reset_module_name": {"type": "string", "children": None},
                "reset_total_questions": {"type": "number", "children": None},
                "reset_module_concepts": {"type": "string", "children": None}
            }
            print("  Patched: code_exam_bilan")

        # --- LLM nodes ---
        # Modèle commun pour les 3 nœuds non-exam (groq-standard = Llama 3.3 70B gratuit)
        GROQ_STANDARD_MODEL = {
            "provider": "langgenius/openai_api_compatible/openai_api_compatible",
            "name": "groq-standard",
            "mode": "chat",
            "completion_params": {"temperature": 0.7, "max_tokens": 400}
        }

        if nid == "llm_plan_choice":
            data["prompt_template"] = [{"id": "plan-prompt", "role": "system", "text": PROMPT_PLAN, "edition_type": "basic"}]
            data["prompt_config"] = {"jinja2_variables": []}
            data["model"] = GROQ_STANDARD_MODEL
            print("  Patched: llm_plan_choice (groq-standard)")

        if nid == "llm_session":
            data["prompt_template"] = [{"id": "session-prompt", "role": "system", "text": PROMPT_SESSION, "edition_type": "basic"}]
            data["prompt_config"] = {"jinja2_variables": []}
            data["model"] = {**GROQ_STANDARD_MODEL, "completion_params": {"temperature": 0.7, "max_tokens": 600}}
            print("  Patched: llm_session (groq-standard)")

        if nid == "llm_onboarding":
            data["prompt_template"] = [{"id": "onboarding-prompt", "role": "system", "text": PROMPT_ONBOARDING, "edition_type": "basic"}]
            data["prompt_config"] = {"jinja2_variables": []}
            data["model"] = GROQ_STANDARD_MODEL
            print("  Patched: llm_onboarding (groq-standard)")

        if nid == "llm_exam":
            data["prompt_template"] = [{"id": "exam-prompt", "role": "system", "text": PROMPT_EXAM, "edition_type": "basic"}]
            data["prompt_config"] = {"jinja2_variables": []}
            # gpt-4o-mini : meilleure instruction following pour l'examen (mistral-small ignorait les règles)
            data["model"] = {
                "provider": "langgenius/openai_api_compatible/openai_api_compatible",
                "name": "gpt-4o-mini",
                "mode": "chat",
                "completion_params": {"temperature": 0.2, "max_tokens": 400}
            }
            print("  Patched: llm_exam (gpt-4o-mini)")

        # --- IF-ELSE nodes ---
        if nid == "if_eval_ready":
            node["data"] = {
                "type": "if-else", "title": "Diagnostic ready?",
                "cases": [{"id": "eval_true", "case_id": "eval_true",
                    "conditions": [{"value": "true", "varType": "boolean",
                        "variable_selector": ["code_eval_check", "eval_ready"],
                        "comparison_operator": "="}],
                    "logical_operator": "and"}],
                "selected": False
            }
            print("  Patched: if_eval_ready")

        if nid == "if_exam_active":
            node["data"] = {
                "type": "if-else", "title": "Mode examen ?",
                "cases": [{"id": "exam_on", "case_id": "exam_on",
                    "conditions": [{"value": "off", "varType": "string",
                        "variable_selector": ["conversation", "exam_mode"],
                        "comparison_operator": "is not"}],
                    "logical_operator": "and"}],
                "selected": False
            }
            print("  Patched: if_exam_active")

        if nid == "if_exam_complete":
            node["data"] = {
                "type": "if-else", "title": "Examen termine ?",
                "cases": [{"id": "exam_done", "case_id": "exam_done",
                    "conditions": [{"value": "true", "varType": "boolean",
                        "variable_selector": ["code_exam_track", "exam_complete"],
                        "comparison_operator": "is"}],
                    "logical_operator": "and"}],
                "selected": False
            }
            print("  Patched: if_exam_complete")

        # --- Answer nodes ---
        if nid == "answer_onboarding":
            data["answer"] = "{{#code_eval_check.cleaned_text#}}"
            print("  Patched: answer_onboarding")

        if nid == "answer_session":
            data["answer"] = "{{#code_exam_detect.cleaned_text#}}"
            print("  Patched: answer_session")

        if nid == "answer_exam":
            data["answer"] = "{{#code_exam_track.cleaned_text#}}"
            print("  Patched: answer_exam")

        if nid == "answer_exam_bilan":
            data["answer"] = "{{#code_exam_bilan.bilan_text#}}"
            print("  Patched: answer_exam_bilan")

        # --- Assigner nodes ---
        if nid == "var_assigner_exam":
            node["data"] = {
                "type": "assigner", "title": "Update Exam Vars", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "exam_mode"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_track", "new_exam_mode"]},
                    {"variable_selector": ["conversation", "exam_question_num"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_track", "new_question_num"]},
                    {"variable_selector": ["conversation", "exam_responses"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_track", "new_responses"]}
                ],
                "selected": False
            }
            print("  Patched: var_assigner_exam (over-write)")

        if nid == "var_assigner_exam_start":
            node["data"] = {
                "type": "assigner", "title": "Set Exam Start", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "exam_mode"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "new_exam_mode"]},
                    {"variable_selector": ["conversation", "exam_module_index"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_module_index"]},
                    {"variable_selector": ["conversation", "exam_module_total"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_module_total"]},
                    {"variable_selector": ["conversation", "exam_module_name"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_module_name"]},
                    {"variable_selector": ["conversation", "exam_total_questions"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_total_questions"]},
                    {"variable_selector": ["conversation", "exam_module_concepts"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_module_concepts"]},
                    {"variable_selector": ["conversation", "exam_modules"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_detect", "exam_modules"]},
                    # Geler le niveau au moment du [EXAM_START] — evite hallucination nom module apres promotion
                    {"variable_selector": ["conversation", "exam_niveau_from"], "operation": "over-write", "input_type": "variable", "value": ["code_turn_check", "niveau"]},
                    {"variable_selector": ["conversation", "exam_niveau_to"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "next_niveau"]}
                ],
                "selected": False
            }
            print("  Patched: var_assigner_exam_start (over-write + module vars + niveau freeze)")

        if nid == "var_assigner_exam_reset":
            node["data"] = {
                "type": "assigner", "title": "Reset/Next Module", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "exam_mode"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_exam_mode"]},
                    {"variable_selector": ["conversation", "exam_question_num"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_question_num"]},
                    {"variable_selector": ["conversation", "exam_responses"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_responses"]},
                    {"variable_selector": ["conversation", "exam_module_index"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_module_index"]},
                    {"variable_selector": ["conversation", "exam_module_name"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_module_name"]},
                    {"variable_selector": ["conversation", "exam_total_questions"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_total_questions"]},
                    {"variable_selector": ["conversation", "exam_module_concepts"], "operation": "over-write", "input_type": "variable", "value": ["code_exam_bilan", "reset_module_concepts"]}
                ],
                "selected": False
            }
            print("  Patched: var_assigner_exam_reset (dynamic from bilan)")

        # --- HTTP exam scoring ---
        if nid == "http_exam_scoring":
            node["data"] = {
                "type": "http-request", "title": "Score Exam (n8n)",
                "url": "http://n8n-academie:5678/webhook/dify-exam-scoring",
                "method": "post",
                "body": {"type": "json", "data": [{"key": "", "type": "text",
                    "value": '{"username": "{{#sys.user_id#}}", "domaine": "anglais", "conversation_id": "{{#sys.conversation_id#}}", "niveau": "{{#code_turn_check.niveau#}}", "concept_keys": "{{#code_profil_check.concept_keys_json#}}", "module_index": {{#conversation.exam_module_index#}}, "module_total": {{#conversation.exam_module_total#}}, "module_name": "{{#conversation.exam_module_name#}}", "module_concepts": "{{#conversation.exam_module_concepts#}}"}'}]},
                "headers": "", "params": "",
                "timeout": {"max_read_timeout": 90, "max_write_timeout": 0, "max_connect_timeout": 0},
                "authorization": {"type": "no-auth", "config": None},
                "selected": False,
                "retry_config": {"max_retries": 2, "retry_enabled": True, "retry_interval": 500}
            }
            print("  Patched: http_exam_scoring")

    # --- Create NEW nodes if missing ---
    NEW_NODES = {
        "if_resume_exam": {
            "data": {
                "type": "if-else", "title": "Resume/Recovery?",
                "cases": [
                    {"id": "resume_yes", "case_id": "resume_yes",
                        "conditions": [{"value": "true", "varType": "boolean",
                            "variable_selector": ["code_turn_check", "exam_resume_needed"],
                            "comparison_operator": "="}],
                        "logical_operator": "and"},
                    {"id": "scoring_recovery", "case_id": "scoring_recovery",
                        "conditions": [{"value": "true", "varType": "boolean",
                            "variable_selector": ["code_turn_check", "scoring_recovery"],
                            "comparison_operator": "="}],
                        "logical_operator": "and"}
                ],
                "selected": False
            },
            "position": {"x": 620, "y": -100},
            "type": "custom"
        },
        "var_assigner_exam_resume": {
            "data": {
                "type": "assigner", "title": "Resume Exam State", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "exam_mode"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_mode"]},
                    {"variable_selector": ["conversation", "exam_question_num"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_question_num"]},
                    {"variable_selector": ["conversation", "exam_responses"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_responses"]},
                    {"variable_selector": ["conversation", "exam_module_index"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_module_index"]},
                    {"variable_selector": ["conversation", "exam_module_total"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_module_total"]},
                    {"variable_selector": ["conversation", "exam_module_name"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_module_name"]},
                    {"variable_selector": ["conversation", "exam_module_concepts"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_module_concepts"]},
                    {"variable_selector": ["conversation", "exam_total_questions"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_total_questions"]},
                    {"variable_selector": ["conversation", "exam_modules"], "operation": "over-write", "input_type": "variable", "value": ["code_profil_check", "exam_resume_modules_json"]}
                ],
                "selected": False
            },
            "position": {"x": 820, "y": -200},
            "type": "custom"
        },
        "var_assigner_scoring_recovery": {
            "data": {
                "type": "assigner", "title": "Reset Scoring Stuck", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "exam_mode"], "operation": "set", "input_type": "constant", "value": "off"},
                    {"variable_selector": ["conversation", "exam_question_num"], "operation": "set", "input_type": "constant", "value": 0},
                    {"variable_selector": ["conversation", "exam_responses"], "operation": "set", "input_type": "constant", "value": "[]"}
                ],
                "selected": False
            },
            "position": {"x": 820, "y": 0},
            "type": "custom"
        },
        "code_exam_persist": {
            "data": {
                "type": "code", "title": "Build Persist Body",
                "code": CODE_EXAM_PERSIST,
                "code_language": "python3",
                "variables": [
                    {"variable": "new_exam_mode", "value_selector": ["code_exam_track", "new_exam_mode"]},
                    {"variable": "new_question_num", "value_selector": ["code_exam_track", "new_question_num"]},
                    {"variable": "new_responses", "value_selector": ["code_exam_track", "new_responses"]},
                    {"variable": "module_index", "value_selector": ["conversation", "exam_module_index"]},
                    {"variable": "module_total", "value_selector": ["conversation", "exam_module_total"]},
                    {"variable": "module_name", "value_selector": ["conversation", "exam_module_name"]},
                    {"variable": "module_concepts", "value_selector": ["conversation", "exam_module_concepts"]},
                    {"variable": "total_questions", "value_selector": ["conversation", "exam_total_questions"]},
                    {"variable": "modules_json", "value_selector": ["conversation", "exam_modules"]},
                    {"variable": "username", "value_selector": ["sys", "user_id"]}
                ],
                "outputs": {"persist_body": {"type": "string", "children": None}},
                "selected": False
            },
            "position": {"x": 2200, "y": -200},
            "type": "custom"
        },
        "http_exam_persist": {
            "data": {
                "type": "http-request", "title": "Persist Exam (n8n)",
                "url": "http://n8n-academie:5678/webhook/dify-exam-persist",
                "method": "post",
                "body": {"type": "json", "data": [{"key": "", "type": "text",
                    "value": "{{#code_exam_persist.persist_body#}}"}]},
                "headers": "", "params": "",
                "timeout": {"max_read_timeout": 10, "max_write_timeout": 0, "max_connect_timeout": 0},
                "authorization": {"type": "no-auth", "config": None},
                "selected": False,
                "retry_config": {"max_retries": 1, "retry_enabled": True, "retry_interval": 300}
            },
            "position": {"x": 2400, "y": -200},
            "type": "custom"
        },
        "http_scoring_recovery_clear": {
            "data": {
                "type": "http-request", "title": "Clear Scoring Stuck (n8n)",
                "url": "http://n8n-academie:5678/webhook/dify-exam-persist",
                "method": "post",
                "body": {"type": "json", "data": [{"key": "", "type": "text",
                    "value": "{\"username\": \"{{#sys.user_id#}}\", \"domaine\": \"anglais\", \"clear\": true}"}]},
                "headers": "", "params": "",
                "timeout": {"max_read_timeout": 10, "max_write_timeout": 0, "max_connect_timeout": 0},
                "authorization": {"type": "no-auth", "config": None},
                "selected": False,
                "retry_config": {"max_retries": 1, "retry_enabled": True, "retry_interval": 300}
            },
            "position": {"x": 820, "y": 160},
            "type": "custom"
        },
        "var_assigner_review_start": {
            "data": {
                "type": "assigner", "title": "Set Review Mode", "version": "2",
                "items": [
                    {"variable_selector": ["conversation", "review_mode"], "operation": "over-write",
                     "input_type": "variable", "value": ["code_exam_detect", "review_mode_value"]}
                ],
                "selected": False
            },
            "position": {"x": 1800, "y": 300},
            "type": "custom"
        }
    }

    for node_id, node_def in NEW_NODES.items():
        if node_id not in existing_ids:
            new_node = {"id": node_id, **node_def}
            nodes.append(new_node)
            existing_ids.add(node_id)
            print(f"  Created: {node_id}")
        else:
            # Patch existing node data
            for n in nodes:
                if n["id"] == node_id:
                    n["data"] = node_def["data"]
                    print(f"  Patched: {node_id}")
                    break

    # --- Fix ALL edges (definitive list) ---
    EXPECTED_EDGES = [
        # Base flow
        ("1775343637677", "1775343918798", None, "start", "http-request"),
        ("1775343918798", "code_profil_check", None, "http-request", "code"),
        ("code_profil_check", "if_profil", None, "code", "if-else"),
        ("if_profil", "code_turn_check", "cas1", "if-else", "code"),
        ("if_profil", "llm_onboarding", "false", "if-else", "llm"),
        # Resume/Recovery gate (NEW)
        ("code_turn_check", "if_resume_exam", None, "code", "if-else"),
        ("if_resume_exam", "var_assigner_exam_resume", "resume_yes", "if-else", "assigner"),
        ("var_assigner_exam_resume", "if_exam_active", None, "assigner", "if-else"),
        ("if_resume_exam", "var_assigner_scoring_recovery", "scoring_recovery", "if-else", "assigner"),
        ("var_assigner_scoring_recovery", "http_scoring_recovery_clear", None, "assigner", "http-request"),
        ("http_scoring_recovery_clear", "if_first_turn", None, "http-request", "if-else"),
        ("if_resume_exam", "if_exam_active", "false", "if-else", "if-else"),
        # Exam gate
        ("if_exam_active", "llm_exam", "exam_on", "if-else", "llm"),
        ("if_exam_active", "if_first_turn", "false", "if-else", "if-else"),
        # Normal session
        ("if_first_turn", "llm_plan_choice", "first", "if-else", "llm"),
        ("if_first_turn", "llm_session", "false", "if-else", "llm"),
        ("llm_plan_choice", "answer_plan", None, "llm", "answer"),
        ("llm_session", "code_exam_detect", None, "llm", "code"),
        ("code_exam_detect", "answer_session", None, "code", "answer"),
        ("code_exam_detect", "var_assigner_exam_start", None, "code", "assigner"),
        ("code_exam_detect", "var_assigner_review_start", None, "code", "assigner"),
        # Var assigner (nb_interactions) — from all LLM paths
        ("llm_plan_choice", "var_assigner", None, "llm", "assigner"),
        ("llm_session", "var_assigner", None, "llm", "assigner"),
        ("llm_onboarding", "var_assigner", None, "llm", "assigner"),
        ("llm_exam", "var_assigner", None, "llm", "assigner"),
        # Snapshot chain
        ("var_assigner", "code_check", None, "assigner", "code"),
        ("code_check", "if_snap", None, "code", "if-else"),
        ("if_snap", "http_snapshot", "true", "if-else", "http-request"),
        ("http_snapshot", "parse_snapshot", None, "http-request", "code"),
        ("parse_snapshot", "store_snapshot", None, "code", "assigner"),
        ("store_snapshot", "http_profil_update", None, "assigner", "http-request"),
        # Onboarding diagnostic pipeline
        ("llm_onboarding", "code_eval_check", None, "llm", "code"),
        ("code_eval_check", "answer_onboarding", None, "code", "answer"),
        ("code_eval_check", "if_eval_ready", None, "code", "if-else"),
        ("if_eval_ready", "http_diagnostic", "eval_true", "if-else", "http-request"),
        # Exam flow
        ("llm_exam", "code_exam_track", None, "llm", "code"),
        ("code_exam_track", "var_assigner_exam", None, "code", "assigner"),
        ("code_exam_track", "if_exam_complete", None, "code", "if-else"),
        ("if_exam_complete", "answer_exam", "false", "if-else", "answer"),
        ("if_exam_complete", "http_exam_scoring", "exam_done", "if-else", "http-request"),
        # Exam persist (NEW) — save state after each question
        ("code_exam_track", "code_exam_persist", None, "code", "code"),
        ("code_exam_persist", "http_exam_persist", None, "code", "http-request"),
        # Scoring pipeline
        ("http_exam_scoring", "code_exam_bilan", None, "http-request", "code"),
        ("code_exam_bilan", "answer_exam_bilan", None, "code", "answer"),
        ("code_exam_bilan", "var_assigner_exam_reset", None, "code", "assigner"),
    ]

    new_edges = []
    for i, (src, tgt, handle, src_type, tgt_type) in enumerate(EXPECTED_EDGES):
        e = {
            "id": f"edge-v11-{i:02d}",
            "source": src, "target": tgt,
            "type": "custom",
            "data": {"sourceType": src_type, "targetType": tgt_type}
        }
        if handle:
            e["sourceHandle"] = handle
        new_edges.append(e)

    graph["edges"] = new_edges
    print(f"  Edges: {len(new_edges)} (replaced)")

    return graph


# ============================================================
# CONVERSATION VARIABLES — add review_mode if missing
# ============================================================

def add_conversation_variable(workflow_id, var_name, var_type, default_value, description):
    """Add a conversation variable to workflows.conversation_variables if not present."""
    import uuid as _uuid
    result = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT conversation_variables FROM workflows WHERE id='{workflow_id}';"],
        capture_output=True, text=True
    )
    raw = result.stdout.strip().replace('\n', '').replace(' +', '').replace('+', '')
    # Remove psql trailing whitespace artifacts
    import re
    raw = re.sub(r'\s+', ' ', raw).strip()
    try:
        conv_vars = json.loads(raw)
    except Exception as e:
        print(f"  [WARN] Could not parse conversation_variables for {workflow_id}: {e}")
        conv_vars = {}

    if var_name in conv_vars:
        print(f"  Conv var '{var_name}' already exists in {workflow_id}")
        return

    new_var = {
        "value_type": var_type,
        "value": default_value,
        "id": str(_uuid.uuid4()),
        "name": var_name,
        "description": description,
        "selector": ["conversation", var_name]
    }
    conv_vars[var_name] = new_var
    conv_json = json.dumps(conv_vars, ensure_ascii=False)
    conv_sql = conv_json.replace("'", "''")
    sql = f"UPDATE workflows SET conversation_variables = '{conv_sql}'::jsonb WHERE id = '{workflow_id}';"
    r = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    if r.returncode == 0:
        print(f"  [OK] Added conv var '{var_name}' to {workflow_id}")
    else:
        print(f"  [ERR] {r.stderr.strip()}")


# ============================================================
# APPLY
# ============================================================

for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Updating {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\n=== Adding conversation variable: review_mode ===")
for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    add_conversation_variable(
        wf_id, "review_mode", "string", "",
        "Mode revision actif (active = review demande par eleve, vide = normal)"
    )

print("\n=== Adding conversation variables: exam_niveau_from / exam_niveau_to ===")
for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    add_conversation_variable(
        wf_id, "exam_niveau_from", "string", "",
        "Niveau de depart gele au moment du EXAM_START (evite hallucination apres promotion)"
    )
    add_conversation_variable(
        wf_id, "exam_niveau_to", "string", "",
        "Niveau cible gele au moment du EXAM_START"
    )

print("\nDone. Restart Dify: docker restart dify-api dify-worker")
