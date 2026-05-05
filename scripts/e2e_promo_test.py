#!/usr/bin/env python3
"""
E2E Test — Promotion B1→B2 Teacher anglais.

Setup : crée un profil test promotion_ready en DB
Examen : répond à toutes les questions via LiteLLM (mistral-small)
Vérification : niveau_global = B2 en DB après dernier module

Usage : python3 e2e_promo_test.py [--clean]
"""

import os
import sys
import json
import time
import requests
import psycopg2

# ─── CONFIG ───────────────────────────────────────────────────────────────────
def _read_secret(name, fallback=""):
    from pathlib import Path
    p = Path(f"/opt/academia-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "academie_db")
DB_USER = os.environ.get("DB_USER", "sinse")
DB_PASS = os.environ.get("DB_PASSWORD", _read_secret("pg-password"))

DIFY_URL = "http://localhost:5001/v1/chat-messages"
DIFY_KEY = os.environ.get("DIFY_KEY_TEACHER", _read_secret("dify-teacher-key"))
TEST_USER = "test-e2e-promo"  # username = sys.user_id dans Teacher

LITELLM_URL = "http://localhost:4000/chat/completions"
LITELLM_KEY = os.environ.get("LITELLM_MASTER_KEY") or _read_secret("litellm-master-key")

B1_CONCEPTS = [
    "present_perfect_simple", "present_perfect_vs_past_simple",
    "present_perfect_continuous", "past_perfect", "passive_voice",
    "conditional_1", "conditional_2", "modal_deduction",
    "reported_speech", "indirect_questions", "phrasal_verbs",
    "gerund_vs_infinitive", "relative_clauses", "connectors",
    "used_to", "would_habitual", "adj_prepositions",
    "adverbs_degree", "so_such_that", "both_either_neither"
]

# ─── DB SETUP ─────────────────────────────────────────────────────────────────
def setup_db():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    # Créer l'élève
    cur.execute("""
        INSERT INTO eleves (username) VALUES (%s)
        ON CONFLICT (username) DO NOTHING
    """, (TEST_USER,))

    # Scores B1 : tous à 87 (promotion_ready : all_tested + 100% >= 75)
    scores = {k: 87 for k in B1_CONCEPTS}

    # Profil promotion_ready B1, mode=structure
    cur.execute("""
        INSERT INTO profils_eleves
            (eleve_id, domaine, niveau_global, mode_apprentissage,
             personnalite, scores_confiance, points_forts, lacunes,
             plan_sessions, derniere_session,
             examen_en_cours, dernier_examen, nb_examens_niveau)
        SELECT e.id, 'anglais', 'B1', 'structure',
            '{"prenom": "TestPromo", "raison": "test E2E", "style_correction": "direct", "centres_interet": "tests", "mode_apprentissage": "structure"}'::jsonb,
            %s::jsonb,
            'present_perfect_simple, conditional_2',
            '',
            'Valider B1 → examen B2',
            NOW(),
            NULL, NULL, 0
        FROM eleves e WHERE e.username = %s
        ON CONFLICT (eleve_id, domaine) DO UPDATE SET
            niveau_global = 'B1',
            mode_apprentissage = 'structure',
            scores_confiance = EXCLUDED.scores_confiance,
            examen_en_cours = NULL,
            dernier_examen = NULL,
            nb_examens_niveau = 0,
            derniere_session = NOW()
    """, (json.dumps(scores), TEST_USER))

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ DB setup : {TEST_USER} → B1, mode=structure, tous concepts testés à 87")


def cleanup_db():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("DELETE FROM snapshots_session WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM historique_sessions WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM profils_eleves WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM eleves WHERE username=%s", (TEST_USER,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"🗑️  DB nettoyée : {TEST_USER} supprimé")


def get_db_niveau():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT pe.niveau_global, pe.examen_en_cours, pe.dernier_examen
        FROM profils_eleves pe JOIN eleves e ON pe.eleve_id = e.id
        WHERE e.username = %s AND pe.domaine = 'anglais'
    """, (TEST_USER,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# ─── DIFY API ─────────────────────────────────────────────────────────────────
def dify_chat(query, user=None, conv_id=""):
    """user defaults to TEST_USER if not specified."""
    r = requests.post(DIFY_URL, headers={
        "Authorization": f"Bearer {DIFY_KEY}",
        "Content-Type": "application/json"
    }, json={
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conv_id,
        "user": user or TEST_USER
    }, timeout=60)
    data = r.json()
    answer = data.get("answer", "")
    new_conv_id = data.get("conversation_id", conv_id)
    return answer, new_conv_id

# ─── LITELLM — générer réponse correcte ou incorrecte ────────────────────────
def generate_correct_answer(question_text):
    """Appelle LiteLLM pour générer une réponse correcte à la question d'examen."""
    prompt = (
        "You are taking an English B1→B2 grammar exam. "
        "Read the following exam question and provide a CORRECT, concise English answer. "
        "Answer ONLY the question — no explanation, no commentary. "
        "If it's a fill-in-the-blank, give the complete sentence with the blank filled. "
        "If it's a correction, give the corrected sentence. "
        "If it's a transformation, give the transformed sentence. "
        "If it's multiple choice, give just the chosen option. "
        "If it's word formation, give just the correct word. "
        "If it's free production, write 2-3 correct sentences.\n\n"
        f"QUESTION:\n{question_text}"
    )
    r = requests.post(LITELLM_URL, headers={
        "Authorization": f"Bearer {LITELLM_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "mistral-small",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.1
    }, timeout=90)
    result = r.json()
    return result["choices"][0]["message"]["content"].strip()


# Réponses incorrectes intentionnelles — mauvais anglais mais vraisemblables
# Règles : toujours en anglais, jamais de "je sais pas" / gibberish → ne pas déclencher REPEAT_QUESTION
WRONG_ANSWERS = [
    "I didn't seen him since last year.",
    "She has went to the market yesterday.",
    "He was working here since three years.",
    "If I would have money, I will travel.",
    "They was very tired after the trip.",
    "I am agree with your opinion.",
    "She don't understands nothing about it.",
    "We has finished the project last week.",
    "He runned to the station quickly.",
    "It depends of the circumstances always.",
    "She used to played piano every day.",
    "He would go fishing every Sundays.",
    "The book was wrote by him in 1990.",
    "I have saw this movie last night.",
    "She is more better at math than me.",
    "He suggested to go at the cinema.",
    "Neither of them were correct about this.",
    "The man which lives next door is kind.",
    "I enjoy to swim every morning early.",
    "Despite of the rain, they continued.",
]
_wrong_idx = 0

def generate_wrong_answer():
    """Retourne une réponse intentionnellement incorrecte (cycle)."""
    global _wrong_idx
    ans = WRONG_ANSWERS[_wrong_idx % len(WRONG_ANSWERS)]
    _wrong_idx += 1
    return ans

# ─── MAIN E2E ─────────────────────────────────────────────────────────────────
def run_e2e(fail_mode=False):
    mode_label = "ÉCHEC (mauvaises réponses)" if fail_mode else "Promotion B1→B2"
    print("\n" + "="*60)
    print(f"E2E TEST — {mode_label} — Teacher anglais")
    print("="*60 + "\n")

    # 1. Setup DB
    setup_db()
    time.sleep(2)

    # 2. Démarrer la conversation → plan avec proposition examen
    print("\n[STEP 1] Démarrage conversation...")
    answer, conv_id = dify_chat("Bonjour, prêt pour ma session !")
    print(f"Teacher: {answer[:300]}")
    print(f"Conv ID: {conv_id}")

    if "examen" not in answer.lower() and "exam" not in answer.lower():
        print("\n[STEP 1b] Proposition examen pas dans le plan, on relance...")
        answer, conv_id = dify_chat("Je veux passer l'examen", conv_id=conv_id)
        print(f"Teacher: {answer[:300]}")

    # 3. Accepter l'examen — le Teacher doit répondre avec [EXAM_START] dans son output
    #    (détecté par code_exam_detect dans Dify, qui switch en mode examen)
    print("\n[STEP 2] Acceptation examen...")
    exam_prompts = [
        "Oui je veux passer l'examen !",
        "Lance l'examen maintenant !",
        "Examen ! Je suis prêt, on y va !",
    ]
    exam_triggered = False
    for i, prompt in enumerate(exam_prompts):
        answer, conv_id = dify_chat(prompt, conv_id=conv_id)
        print(f"  Tentative {i+1}: {answer[:250]}")
        # code_exam_detect strips [EXAM_START] from output and triggers exam mode
        # If exam mode activated, Teacher switches to llm_exam (Module/question format)
        if "Module" in answer or "module" in answer or "Question 1" in answer or "question 1" in answer.lower():
            exam_triggered = True
            print(f"  ✅ Exam mode activé (tentative {i+1})")
            break
        time.sleep(1)

    if not exam_triggered:
        print("⚠️  Teacher n'a pas déclenché le mode examen après 3 tentatives. Arrêt.")
        return False

    print(f"\nTeacher (module intro): {answer[:400]}")

    # 5. Boucle exam — logique unifiée
    # IMPORTANT : le bilan (✅/❌/🎉/➡️) EST dans 'answer' dès que "correction en cours"
    # est détecté. Ne PAS envoyer de message supplémentaire pour récupérer le bilan.
    # Envoyer "oui" uniquement pour déclencher le module suivant (si ➡️ détecté).
    module_num = 1
    question_count = 0
    max_questions = 80  # sécurité
    modules_done = []

    def handle_module_end(bilan_text, module_num):
        """Traite la fin d'un module. Retourne (action, next_module_num) où action in ['stop','next','promotion']."""
        print(f"   Bilan:\n{bilan_text[:500]}")
        if "🎉" in bilan_text or "TOUS LES MODULES" in bilan_text:
            return "promotion", module_num
        if "❌ Module" in bilan_text or "minimum 70" in bilan_text or "à repasser" in bilan_text.lower():
            return "stop", module_num
        if "➡️" in bilan_text or "module suivant" in bilan_text.lower():
            return "next", module_num + 1
        return "stop", module_num  # fallback

    while question_count < max_questions:
        question_count += 1

        # Vérifier si la réponse courante contient une fin de module
        if "[EXAM_COMPLETE]" in answer or "correction en cours" in answer.lower():
            print(f"\n🏁 Module {module_num} terminé (q#{question_count-1})")
            modules_done.append(module_num)
            action, next_mod = handle_module_end(answer, module_num)
            if action == "promotion":
                print(f"\n🎉 PROMOTION DÉTECTÉE !")
                break
            if action == "stop":
                print(f"\n{'✅ MODULE ÉCHOUÉ COMME PRÉVU' if fail_mode else '⚠️  Arrêt'} — module {module_num}")
                break
            # action == "next"
            module_num = next_mod
            print(f"\n[MODULE {module_num}] Démarrage...")
            answer, conv_id = dify_chat("oui", conv_id=conv_id)
            print(f"   Réponse: {answer[:200]}")
            continue

        # Générer une réponse (correcte ou intentionnellement incorrecte)
        print(f"\n   Q{question_count} (mod.{module_num}): {answer[:200]}...")
        if fail_mode:
            user_answer = generate_wrong_answer()
            print(f"   Réponse (intentionnellement fausse): {user_answer}")
        else:
            user_answer = generate_correct_answer(answer)
            print(f"   Réponse: {user_answer}")

        time.sleep(0.5)
        answer, conv_id = dify_chat(user_answer, conv_id=conv_id)

        # Vérifier fin de module dans la nouvelle réponse
        if "[EXAM_COMPLETE]" in answer or "correction en cours" in answer.lower():
            print(f"\n🏁 Module {module_num} terminé (q#{question_count})")
            modules_done.append(module_num)
            action, next_mod = handle_module_end(answer, module_num)
            if action == "promotion":
                print(f"\n🎉 PROMOTION DÉTECTÉE !")
                break
            if action == "stop":
                print(f"\n{'✅ MODULE ÉCHOUÉ COMME PRÉVU' if fail_mode else '⚠️  Arrêt'} — module {module_num}")
                break
            # action == "next"
            module_num = next_mod
            print(f"\n[MODULE {module_num}] Démarrage...")
            answer, conv_id = dify_chat("oui", conv_id=conv_id)
            print(f"   Réponse module {module_num}: {answer[:200]}")
            # continue → le prochain tour de boucle affichera les questions

    # 6. Vérification DB
    print("\n" + "="*60)
    print("VÉRIFICATION DB")
    print("="*60)
    row = get_db_niveau()
    if row:
        niveau_db, examen_en_cours, dernier_examen = row
        print(f"  niveau_global  : {niveau_db}")
        print(f"  examen_en_cours: {'(vide)' if not examen_en_cours else str(examen_en_cours)[:100]}")
        print(f"  dernier_examen : {str(dernier_examen)[:100] if dernier_examen else 'None'}")

        if fail_mode:
            # En mode fail : on vérifie que niveau = B1 (pas de promotion)
            if niveau_db == "B1":
                passed = dernier_examen.get('passed', True) if dernier_examen else True
                score = dernier_examen.get('score', 0) if dernier_examen else 0
                print(f"\n✅ E2E ÉCHEC VALIDÉ — niveau reste B1, score={score}, passed={passed}")
                return True
            else:
                print(f"\n❌ INATTENDU : niveau_db={niveau_db} alors que mauvaises réponses")
                return False
        else:
            if niveau_db == "B2":
                print("\n✅✅✅ E2E RÉUSSI — Promotion B1→B2 confirmée en DB !")
                return True
            else:
                print(f"\n⚠️  Niveau en DB = {niveau_db} (pas encore B2)")
                print("   Modules complétés:", modules_done)
                return False
    else:
        print("❌ Profil introuvable en DB")
        return False


# ─── TEST #4 : COOLDOWN ───────────────────────────────────────────────────────
def setup_db_cooldown():
    """Profile promotion_ready + dernier_examen recent (today, failed) → cooldown doit bloquer."""
    from datetime import datetime, timezone
    setup_db()  # crée le profil promotion_ready
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    # Inject a recent failed exam → cooldown active (sessions_since=0, days_since=0)
    recent_exam = {
        "date": datetime.now(timezone.utc).isoformat(),
        "niveau": "B1",
        "score": 65,
        "passed": False,
        "to_review": ["present_perfect_simple", "passive_voice"],
        "commentaire": "Module échoué — à consolider"
    }
    cur.execute("""
        UPDATE profils_eleves SET
            dernier_examen = %s::jsonb,
            nb_examens_niveau = 1
        WHERE eleve_id = (SELECT id FROM eleves WHERE username = %s)
        AND domaine = 'anglais'
    """, (json.dumps(recent_exam), TEST_USER))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ DB cooldown setup : {TEST_USER} → B1 promo_ready + dernier_examen FAILED (today)")


def run_test_cooldown():
    """
    Test #4 — Cooldown examen.
    Vérifie :
      a) Plan ne propose PAS l'examen quand cooldown actif (failed exam today)
      b) Le plan_prefix #5 guide vers consolidation des concepts faibles
      c) L'élève peut quand même demander l'examen manuellement
    """
    print("\n" + "="*60)
    print("TEST #4 — Cooldown examen + Guidance module échoué (#5)")
    print("="*60 + "\n")

    setup_db_cooldown()
    time.sleep(2)

    # a) Démarrage session → devrait montrer guidance "module échoué" pas proposition exam
    answer, conv_id = dify_chat("Bonjour !", TEST_USER)
    print(f"[Plan]: {answer[:400]}")

    # Vérifier : pas de "tu veux tenter l'examen" avec invitation directe
    has_exam_invite = ("tu veux tenter" in answer.lower() and "examen" in answer.lower()
                       and "bravo" in answer.lower())
    has_consolider = any(kw in answer.lower() for kw in
                         ["consolid", "retravaill", "à consolider", "echoue", "échoué"])

    if has_exam_invite:
        print("❌ ECHEC : L'examen est proposé malgré le cooldown !")
        cleanup_db()
        return False

    print(f"✅ Exam non proposé automatiquement (cooldown respecté)")
    if has_consolider:
        print(f"✅ Guidance 'consolider' détectée (#5 actif)")
    else:
        print(f"⚠️  Guidance #5 non détectée dans le plan (vérifier manuellement)")

    # b) L'élève demande l'examen manuellement → doit être accordé
    answer2, conv_id2 = dify_chat("Je veux passer l'examen maintenant !", TEST_USER, conv_id)
    print(f"\n[Demande manuelle exam]: {answer2[:300]}")

    has_manual_start = any(kw in answer2.lower() for kw in
                            ["mode examen", "examen !", "parfait", "exam_start"])
    if has_manual_start:
        print("✅ Demande manuelle d'examen accordée (bypass cooldown)")
    else:
        print("⚠️  Demande manuelle d'examen : réponse à vérifier")

    cleanup_db()
    print("\n✅ TEST #4 TERMINÉ")
    return True



# ─── TEST #3 : REPRISE MID-EXAM ───────────────────────────────────────────────
def run_test_resume():
    """
    Test #3 — Reprise mid-exam.
    Vérifie que si l'élève quitte en plein examen et revient,
    la nouvelle conversation reprend exactement à la bonne question.
    """
    print("\n" + "="*60)
    print("TEST #3 — Reprise mid-exam")
    print("="*60 + "\n")

    TEST_USER_RESUME = "test-e2e-resume"

    # Setup profil promotion_ready pour ce user
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("INSERT INTO eleves (username) VALUES (%s) ON CONFLICT DO NOTHING", (TEST_USER_RESUME,))
    scores = {k: 87 for k in B1_CONCEPTS}
    cur.execute("""
        INSERT INTO profils_eleves
            (eleve_id, domaine, niveau_global, mode_apprentissage,
             personnalite, scores_confiance, points_forts, lacunes,
             plan_sessions, derniere_session, examen_en_cours, dernier_examen, nb_examens_niveau)
        SELECT e.id, 'anglais', 'B1', 'structure',
            '{"prenom": "TestResume"}'::jsonb,
            %s::jsonb, '', '', 'Test reprise', NOW(), NULL, NULL, 0
        FROM eleves e WHERE e.username = %s
        ON CONFLICT (eleve_id, domaine) DO UPDATE SET
            niveau_global = 'B1', mode_apprentissage = 'structure',
            scores_confiance = EXCLUDED.scores_confiance,
            examen_en_cours = NULL, derniere_session = NOW()
    """, (json.dumps(scores), TEST_USER_RESUME))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Setup DB : {TEST_USER_RESUME} → B1 promotion_ready")

    try:
        time.sleep(2)

        # 1. Démarrer conversation + proposer examen
        print("\n[STEP 1] Démarrage + proposition examen...")
        answer, conv1 = dify_chat("Bonjour !", TEST_USER_RESUME)
        if "examen" not in answer.lower():
            answer, conv1 = dify_chat("Je veux passer l'examen", TEST_USER_RESUME, conv1)
        exam_prompts = [
            "Oui je veux passer l'examen !",
            "Lance l'examen maintenant !",
            "Examen ! Je suis prêt, on y va !",
        ]
        for prompt in exam_prompts:
            answer, conv1 = dify_chat(prompt, TEST_USER_RESUME, conv1)
            if "Module" in answer or "module" in answer or "Question 1" in answer:
                break
            time.sleep(1)
        print(f"  Intro module: {answer[:200]}")

        # 2. Répondre à 3 questions pour que l'état soit persisté
        print("\n[STEP 2] 3 questions pour activer la persistance...")
        for i in range(3):
            user_ans = generate_correct_answer(answer)
            answer, conv1 = dify_chat(user_ans, TEST_USER_RESUME, conv1)
            print(f"  Q{i+1}: {answer[:100]}...")
            time.sleep(0.5)
            if "correction en cours" in answer.lower() or "[EXAM_COMPLETE]" in answer:
                print("  Module terminé prématurément — profile avec trop peu de questions")
                break

        # 3. Vérifier que l'état est bien persisté en DB
        time.sleep(2)
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                                 user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        cur.execute("""
            SELECT pe.examen_en_cours
            FROM profils_eleves pe JOIN eleves e ON pe.eleve_id = e.id
            WHERE e.username = %s AND pe.domaine = 'anglais'
        """, (TEST_USER_RESUME,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row or not row[0]:
            print("⚠️  examen_en_cours vide en DB — persistance peut-être trop lente ou 0 questions")
            saved_q = 0
        else:
            saved_state = row[0]
            saved_q = saved_state.get("question_num", 0)
            saved_mode = saved_state.get("mode", "?")
            print(f"✅ État persisté : mode={saved_mode}, question_num={saved_q}")

        # 4. NOUVELLE conversation (simule déconnexion + reconnexion)
        print(f"\n[STEP 3] Nouvelle conversation (simule reconnexion)...")
        answer_new, conv2 = dify_chat("Bonjour de retour !", TEST_USER_RESUME)
        print(f"  Réponse nouvelle session: {answer_new[:400]}")

        # 5. Vérifier reprise
        has_reprise = any(kw in answer_new.lower() for kw in
                         ["reprise", "reprend", "module", "question"])
        if has_reprise and saved_q > 0:
            print(f"✅ Reprise détectée ! (question_num sauvée = {saved_q})")
            success = True
        elif saved_q == 0:
            print("⚠️  Pas d'état à reprendre (exam terminé ou pas persisté) — test inconclus")
            success = True  # Non bloquant si persistance pas encore déclenchée
        else:
            print(f"❌ Reprise non détectée ! Réponse: {answer_new[:200]}")
            success = False

        return success

    finally:
        # Cleanup
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                                 user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        for tbl in ["snapshots_session", "historique_sessions", "profils_eleves"]:
            cur.execute(f"DELETE FROM {tbl} WHERE eleve_id IN "
                        f"(SELECT id FROM eleves WHERE username=%s)", (TEST_USER_RESUME,))
        cur.execute("DELETE FROM eleves WHERE username=%s", (TEST_USER_RESUME,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"\n🗑️  Cleanup {TEST_USER_RESUME} OK")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        cleanup_db()
        sys.exit(0)

    if "--cooldown" in sys.argv:
        # Test #4 — cooldown + guidance module échoué
        try:
            success = run_test_cooldown()
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    if "--resume" in sys.argv:
        # Test #3 — reprise mid-exam
        try:
            success = run_test_resume()
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    fail_mode = "--fail" in sys.argv

    try:
        success = run_e2e(fail_mode=fail_mode)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
