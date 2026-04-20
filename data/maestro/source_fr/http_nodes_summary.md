# HTTP nodes with domain=en markers

🔴 **Requête HTTP** (node 1775343918798)
  - URL: `http://n8n-academie:5678/webhook/dify-profil-get?username={{#sys.user_id#}}&domain=en`
  - body snippet: `{"data": [], "type": "none"}`

⚪ **Snapshot session** (node http_snapshot)
  - URL: `http://n8n-academie:5678/webhook/dify-snapshot`
  - body snippet: `{"data": [{"key": "", "type": "text", "value": "{\"username\": \"{{#sys.user_id#}}\", \"domain\": \"en\", \"conversation_id\": \"{{#sys.conversation_id#}}\"}"}], "type": "json"}`

⚪ **Maj profil élève** (node http_profil_update)
  - URL: `http://n8n-academie:5678/webhook/dify-profil-update`
  - body snippet: `{"data": [{"key": "", "type": "text", "value": "{\"username\": \"{{#sys.user_id#}}\", \"domain\": \"en\"}"}], "type": "json"}`

⚪ **Diagnostic CECRL** (node http_diagnostic)
  - URL: `http://n8n-academie:5678/webhook/dify-diagnostic`
  - body snippet: `{"type": "json", "data": [{"key": "", "type": "text", "value": "{\"username\": \"{{#sys.user_id#}}\", \"domain\": \"en\", \"conversation_id\": \"{{#sys.conversation_id#}}\"}"}]}`

⚪ **Score Exam (n8n)** (node http_exam_scoring)
  - URL: `http://n8n-academie:5678/webhook/dify-exam-scoring`
  - body snippet: `{"type": "json", "data": [{"key": "", "type": "text", "value": "{\"username\": \"{{#sys.user_id#}}\", \"domain\": \"en\", \"conversation_id\": \"{{#sys.conversation_id#}}\", \"niveau\": \"{{#code_turn`

⚪ **Persist Exam (n8n)** (node http_exam_persist)
  - URL: `http://n8n-academie:5678/webhook/dify-exam-persist`
  - body snippet: `{"type": "json", "data": [{"key": "", "type": "text", "value": "{{#code_exam_persist.persist_body#}}"}]}`

⚪ **Clear Scoring Stuck (n8n)** (node http_scoring_recovery_clear)
  - URL: `http://n8n-academie:5678/webhook/dify-exam-persist`
  - body snippet: `{"type": "json", "data": [{"key": "", "type": "text", "value": "{\"username\": \"{{#sys.user_id#}}\", \"domain\": \"en\", \"clear\": true}"}]}`

