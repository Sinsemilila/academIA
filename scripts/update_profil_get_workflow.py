#!/usr/bin/env python3
"""
Met a jour le workflow n8n dify-profil-get (v5) pour:
1. Retourne concept_keys + scores_confiance + mode_apprentissage
2. Retourne concept_keys du niveau N+1 (pour injection progressive)
3. Retourne examen_en_cours (pour reprise apres coupure)
4. Retourne sessions_depuis_examen (cooldown examen)
5. Retourne concept_weights + concept_groups (examens modulaires)

Usage:
  python3 /opt/academie/scripts/update_profil_get_workflow.py && docker restart n8n-academie
"""

import json
import subprocess

WORKFLOW_ID = "8NnhEQWCSr0octMS"
VERSION_ID = "bc4bc7da-d4a4-4c42-accd-6774e710c917"

nodes = [
    # 1. Webhook (inchange)
    {
        "id": "6336ef18-b932-4b21-a4fe-6370f4b34edf",
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "position": [0, 0],
        "webhookId": "dify-profil-get-webhook-id",
        "parameters": {
            "path": "dify-profil-get",
            "options": {},
            "httpMethod": "GET",
            "responseMode": "responseNode"
        },
        "typeVersion": 2.1
    },
    # 2. SQL (MODIFIE — ajoute concept_keys)
    {
        "id": "3bccca95-e228-44e2-8723-c8d80fc3ee12",
        "name": "Execute a SQL query",
        "type": "n8n-nodes-base.postgres",
        "position": [208, 0],
        "parameters": {
            "operation": "executeQuery",
            "query": """ WITH new_eleve AS (
    INSERT INTO eleves (username)
    VALUES ('{{ $json.query.username }}')
    ON CONFLICT (username) DO NOTHING
  ),
  niveau_map AS (
    SELECT unnest(ARRAY['A1','A2','B1','B2','C1','C2']) as niveau,
           unnest(ARRAY['A2','B1','B2','C1','C2','C2']) as next_niveau
  )
  SELECT
    e.username,
    p.domaine,
    p.niveau_global,
    p.personnalite,
    p.scores_confiance,
    p.points_forts,
    p.lacunes,
    p.plan_sessions,
    p.derniere_session,
    p.mode_apprentissage,
    p.examen_en_cours,
    p.dernier_examen,
    p.nb_examens_niveau,
    s.contenu as dernier_snapshot,
    c.points_cles as curriculum,
    c.concept_keys,
    c.concept_weights,
    c.concept_groups,
    cnext.concept_keys as next_concept_keys,
    nm.next_niveau,
    COALESCE(ss.sessions_count, 0) as sessions_depuis_examen
  FROM eleves e
  LEFT JOIN profils_eleves p ON p.eleve_id = e.id AND p.domaine = '{{ $json.query.domaine }}'
  LEFT JOIN LATERAL (
    SELECT contenu FROM snapshots_session
    WHERE eleve_id = e.id AND domaine = '{{ $json.query.domaine }}'
    ORDER BY created_at DESC LIMIT 1
  ) s ON true
  LEFT JOIN curriculums c ON c.domaine = '{{ $json.query.domaine }}' AND c.niveau = p.niveau_global
  LEFT JOIN niveau_map nm ON nm.niveau = p.niveau_global
  LEFT JOIN curriculums cnext ON cnext.domaine = '{{ $json.query.domaine }}' AND cnext.niveau = nm.next_niveau
  LEFT JOIN LATERAL (
    SELECT COUNT(*) as sessions_count FROM snapshots_session
    WHERE eleve_id = e.id AND domaine = '{{ $json.query.domaine }}'
    AND created_at > COALESCE((p.dernier_examen->>'date')::timestamptz, '1970-01-01'::timestamptz)
  ) ss ON true
  WHERE e.username = '{{ $json.query.username }}'""",
            "options": {}
        },
        "credentials": {
            "postgres": {
                "id": "NpF5tjOzvAWkHR2n",
                "name": "Postgres account"
            }
        },
        "typeVersion": 2.6
    },
    # 3. Code (MODIFIE — retourne aussi concept_keys et scores en JSON)
    {
        "id": "66d125fe-981f-4449-ba0c-1b5e8d5f2a21",
        "name": "Code in JavaScript",
        "type": "n8n-nodes-base.code",
        "position": [416, 0],
        "parameters": {
            "jsCode": r"""const d = $input.first().json;

if (!d.niveau_global) {
  return [{ json: {
    profil_formate: "", concept_keys: [], scores_confiance: {},
    mode_apprentissage: "libre", next_concept_keys: [], next_niveau: "",
    examen_en_cours: null, dernier_examen: null, nb_examens_niveau: 0,
    sessions_depuis_examen: 0,
    concept_weights: {}, concept_groups: {}
  } }];
}

const lignes = ["[PROFIL ELEVE]"];
lignes.push("Niveau : " + d.niveau_global);
lignes.push("Mode : " + (d.mode_apprentissage || "libre"));

if (d.personnalite) {
  const p = typeof d.personnalite === "string" ? JSON.parse(d.personnalite) : d.personnalite;
  if (Object.keys(p).length > 0) {
    if (p.prenom) lignes.push("Prenom : " + p.prenom);
    if (p.style_correction) lignes.push("Style : " + p.style_correction);
    if (p.centres_interet) lignes.push("Interets : " + p.centres_interet);
    if (p.raison) lignes.push("Objectif : " + p.raison);
  }
}

// Scores confiance
let scoresObj = {};
if (d.scores_confiance) {
  scoresObj = typeof d.scores_confiance === "string" ? JSON.parse(d.scores_confiance) : d.scores_confiance;
  if (Object.keys(scoresObj).length > 0) {
    const scoresLines = Object.entries(scoresObj)
      .sort((a,b) => a[1] - b[1])
      .map(([k,v]) => `  ${k}: ${v}/100`);
    lignes.push("Scores confiance :");
    lignes.push(...scoresLines);
  }
}

if (d.points_forts) lignes.push("Points forts : " + d.points_forts);
if (d.lacunes) lignes.push("Lacunes : " + d.lacunes);
if (d.plan_sessions) lignes.push("Plan en cours : " + d.plan_sessions);
if (d.derniere_session) lignes.push("Derniere session : " + d.derniere_session);
if (d.dernier_snapshot) lignes.push("Dernier snapshot : " + d.dernier_snapshot);

// Concept keys du niveau
let conceptKeys = [];
if (d.concept_keys) {
  conceptKeys = typeof d.concept_keys === "string" ? JSON.parse(d.concept_keys) : (d.concept_keys || []);
}

// Concept keys N+1
let nextConceptKeys = [];
if (d.next_concept_keys) {
  nextConceptKeys = typeof d.next_concept_keys === "string" ? JSON.parse(d.next_concept_keys) : (d.next_concept_keys || []);
}

// Examen en cours
let examenEnCours = null;
if (d.examen_en_cours) {
  examenEnCours = typeof d.examen_en_cours === "string" ? JSON.parse(d.examen_en_cours) : d.examen_en_cours;
}

// Dernier examen
let dernierExamen = null;
if (d.dernier_examen) {
  dernierExamen = typeof d.dernier_examen === "string" ? JSON.parse(d.dernier_examen) : d.dernier_examen;
}

// Concept weights & groups (exam modules)
let conceptWeights = {};
if (d.concept_weights) {
  conceptWeights = typeof d.concept_weights === "string" ? JSON.parse(d.concept_weights) : (d.concept_weights || {});
}
let conceptGroups = {};
if (d.concept_groups) {
  conceptGroups = typeof d.concept_groups === "string" ? JSON.parse(d.concept_groups) : (d.concept_groups || {});
}

// Curriculum
if (d.curriculum) {
  const cur = typeof d.curriculum === "string" ? JSON.parse(d.curriculum) : d.curriculum;
  lignes.push("");
  lignes.push("[CURRICULUM " + d.niveau_global + "]");
  if (cur.grammaire) {
    lignes.push("Grammaire : " + cur.grammaire.join(" | "));
  }
  if (cur.erreurs_communes) {
    lignes.push("Erreurs frequentes : " + cur.erreurs_communes.join(" | "));
  }
}

return [{ json: {
  profil_formate: lignes.join("\n"),
  concept_keys: conceptKeys,
  scores_confiance: scoresObj,
  mode_apprentissage: d.mode_apprentissage || "libre",
  next_concept_keys: nextConceptKeys,
  next_niveau: d.next_niveau || "",
  examen_en_cours: examenEnCours,
  dernier_examen: dernierExamen,
  nb_examens_niveau: d.nb_examens_niveau || 0,
  sessions_depuis_examen: parseInt(d.sessions_depuis_examen) || 0,
  concept_weights: conceptWeights,
  concept_groups: conceptGroups,
  derniere_session: d.derniere_session || null
} }];"""
        },
        "typeVersion": 2
    },
    # 4. Respond (inchange)
    {
        "id": "f455603f-f447-40c2-ae1b-be94aec7c66d",
        "name": "Respond to Webhook",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [624, 0],
        "parameters": {
            "respondWith": "allIncomingItems"
        }
    }
]

connections = {
    "Webhook": {
        "main": [[{"node": "Execute a SQL query", "type": "main", "index": 0}]]
    },
    "Execute a SQL query": {
        "main": [[{"node": "Code in JavaScript", "type": "main", "index": 0}]]
    },
    "Code in JavaScript": {
        "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
    }
}

# ============================================================
# BUILD & APPLY
# ============================================================
nodes_json = json.dumps(nodes, ensure_ascii=False)
connections_json = json.dumps(connections, ensure_ascii=False)

nodes_sql = nodes_json.replace("'", "''")
connections_sql = connections_json.replace("'", "''")

sql1 = f"""UPDATE workflow_entity
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE id = '{WORKFLOW_ID}';"""

sql2 = f"""UPDATE workflow_history
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE "versionId" = '{VERSION_ID}';"""

for i, sql in enumerate([sql1, sql2], 1):
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    table = "workflow_entity" if i == 1 else "workflow_history"
    if result.returncode == 0:
        print(f"[OK] {table} updated: {result.stdout.strip()}")
    else:
        print(f"[ERR] {table}: {result.stderr.strip()}")

print("\nDone.")
