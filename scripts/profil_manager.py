import os
import psycopg2
import json
from datetime import datetime
from pathlib import Path

def _read_secret(name, fallback=""):
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "172.16.0.25"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "academie_db"),
    "user": os.environ.get("DB_USER", "sinse"),
    "password": os.environ.get("DB_PASSWORD", _read_secret("pg-password"))
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_or_create_eleve(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM eleves WHERE username = %s", (username,))
    row = cur.fetchone()
    if row:
        eleve_id = row[0]
    else:
        cur.execute("INSERT INTO eleves (username) VALUES (%s) RETURNING id", (username,))
        eleve_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    conn.close()
    return eleve_id

def get_profil(username, domaine):
    eleve_id = get_or_create_eleve(username)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT niveau_global, personnalite, scores_confiance,
               points_forts, lacunes, plan_sessions, derniere_session
        FROM profils_eleves
        WHERE eleve_id = %s AND domaine = %s
    """, (eleve_id, domaine))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {
        "niveau_global": row[0],
        "personnalite": row[1],
        "scores_confiance": row[2],
        "points_forts": row[3],
        "lacunes": row[4],
        "plan_sessions": row[5],
        "derniere_session": str(row[6]) if row[6] else None
    }

def save_profil(username, domaine, profil):
    eleve_id = get_or_create_eleve(username)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profils_eleves
            (eleve_id, domaine, niveau_global, personnalite, scores_confiance,
             points_forts, lacunes, plan_sessions, derniere_session, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (eleve_id, domaine) DO UPDATE SET
            niveau_global = EXCLUDED.niveau_global,
            personnalite = EXCLUDED.personnalite,
            scores_confiance = EXCLUDED.scores_confiance,
            points_forts = EXCLUDED.points_forts,
            lacunes = EXCLUDED.lacunes,
            plan_sessions = EXCLUDED.plan_sessions,
            derniere_session = NOW(),
            updated_at = NOW()
    """, (
        eleve_id, domaine,
        profil.get("niveau_global"),
        json.dumps(profil.get("personnalite", {})),
        json.dumps(profil.get("scores_confiance", {})),
        profil.get("points_forts"),
        profil.get("lacunes"),
        profil.get("plan_sessions")
    ))
    conn.commit()
    cur.close()
    conn.close()

def save_snapshot(username, domaine, contenu):
    eleve_id = get_or_create_eleve(username)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO snapshots_session (eleve_id, domaine, contenu)
        VALUES (%s, %s, %s)
    """, (eleve_id, domaine, contenu))
    conn.commit()
    cur.close()
    conn.close()

def format_profil_for_injection(profil):
    if not profil:
        return ""
    lines = ["[PROFIL ELEVE]"]
    lines.append(f"Niveau global : {profil.get('niveau_global', 'inconnu')}")
    if profil.get("personnalite"):
        lines.append(f"Personnalite Sensei : {json.dumps(profil['personnalite'], ensure_ascii=False)}")
    if profil.get("points_forts"):
        lines.append(f"Points forts : {profil['points_forts']}")
    if profil.get("lacunes"):
        lines.append(f"Lacunes prioritaires : {profil['lacunes']}")
    if profil.get("plan_sessions"):
        lines.append(f"Plan en cours : {profil['plan_sessions']}")
    if profil.get("derniere_session"):
        lines.append(f"Derniere session : {profil['derniere_session']}")
    return "\n".join(lines)

if __name__ == "__main__":
    profil_test = {
        "niveau_global": "C1",
        "personnalite": {"ton": "serieux", "humour": True, "exigence": "challenge"},
        "scores_confiance": {"present_perfect": 85, "conditionnel": 90, "vocabulaire": 80},
        "points_forts": "Vocabulaire riche, structure de phrases complexes, conditionnels",
        "lacunes": "Precision du vocabulaire C1, nuances stylistiques",
        "plan_sessions": "Session 1: nuances vocabulaire C1. Session 2: registres formels. Session 3: debat"
    }
    save_profil("sinse", "anglais", profil_test)
    profil = get_profil("sinse", "anglais")
    print(format_profil_for_injection(profil))
