# code_exam_bilan — ES string substitutions

For use in `maestro_prompts.json` via `clone_app.py --prompts-override`. Each entry must have a **unique context-enriched key** so `str.replace()` doesn't touch unrelated nodes.

## User-visible strings (FR → ES)

| Context | FR literal (as in code) | ES replacement |
|---|---|---|
| Error — scoring failure intro | `"La correction a rencontre un probleme. Votre progression est sauvegardee.\n"` | `"La corrección ha tenido un problema. Tu progreso está guardado.\n"` |
| Error — retry instruction | `"Vous pourrez retenter l'examen lors de votre prochaine session.\n"` | `"Podrás volver a intentar el examen en tu próxima sesión.\n"` |
| Error — apology | `"Toutes mes excuses pour ce desagrement."` | `"Lamento las molestias."` |
| Module passed header | `"\n\n✅ Module "` | `"\n\n✅ Módulo "` |
| Module failed header | `"\n\n❌ Module "` | `"\n\n❌ Módulo "` |
| Module failed suffix | `"/100 (minimum 70)\n"` | `"/100 (mínimo 70)\n"` |
| Next module prompt | `"\n➡️  Module suivant : "` | `"\n➡️  Próximo módulo : "` |
| Questions count | `" questions)\n"` | `" preguntas)\n"` |
| Ready? prompt | `"Prêt(e) ? Répondez 'oui' pour continuer.\n"` | `"¿Listo/a? Responde 'sí' para continuar.\n"` |
| All passed + promotion | `"\n🎉 TOUS LES MODULES RÉUSSIS — Vous passez en "` | `"\n🎉 ¡TODOS LOS MÓDULOS SUPERADOS — Pasas a "` |
| Promotion suffix | `" !\n"` (too generic, only in context after next_level) | KEEP AS-IS (generic punctuation) |
| Review list header | `"\nÀ retravailler : "` | `"\nA repasar : "` |
| Module to redo | `"Ce module est à repasser. On va consolider ça ensemble !\n"` | `"Tienes que volver a hacer este módulo. Vamos a consolidarlo juntos.\n"` |
| Fallback exam text | `"Examen termine."` | `"Examen terminado."` |

## Notes

- `"/100\n"` alone NOT substituted — generic, appears in both passed/failed (differs only by "(minimum 70)" suffix).
- `'oui'` → `'sí'` : quoted literal, the webapp user needs to literally type "sí" to advance. Verify that the downstream parser (Python `if response == "oui"`) also gets its check translated — else user typing "sí" fails. **FLAG : check code_exam_track or similar for `"oui"` literal match.**
