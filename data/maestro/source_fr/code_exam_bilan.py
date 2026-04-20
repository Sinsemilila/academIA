# Format Bilan (node id: code_exam_bilan)
# Code: 5429 chars

import json

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
