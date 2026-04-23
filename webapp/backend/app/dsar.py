"""
Refactor 2026-H2 Phase A6 — DSAR (Data Subject Access Request) helpers.

Two operations exposed via /api/me/* endpoints (cf. settings_router.py) :
  * export_user_data(conn, user_row) -> dict   — full PII dump (RGPD art. 15+20)
  * delete_user_account(conn, user_row)        — hard delete cascade (RGPD art. 17)

Tables touched (FK ordering matters for delete) :
  * user_id  : xp_log, streaks, user_sessions, active_sessions, user_totp, users
  * eleve_id : onboarding_telemetry_events, spaced_retrieval_queue,
               consolidation_events, snapshots_session, error_log,
               learner_profiles, profils_eleves, eleves
  * Dify     : messages, conversations, end_users (joined via dify_user_id)

Sessions Redis are dropped via sessions.delete_all_sessions_for_user().
Cf. dpia.md §1.4 for the full PII inventory and §1.5 for retention policy.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import asyncpg


def _serialize(value: Any) -> Any:
    """Convert PG-native types to JSON-friendly forms."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _rows_to_dicts(rows: list[asyncpg.Record], drop: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        d = {k: _serialize(v) for k, v in dict(row).items() if k not in drop}
        out.append(d)
    return out


async def export_user_data(conn: asyncpg.Connection, user_row: dict) -> dict[str, Any]:
    """Full DSAR export. Returns a dict serializable to JSON.

    Sensitive fields stripped : password_hash, TOTP secret + recovery codes.
    """
    user_id = user_row["id"]
    eleve_id = user_row.get("eleve_id")
    dify_user_id = user_row.get("dify_user_id")

    payload: dict[str, Any] = {
        "_meta": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "username": user_row.get("username"),
            "schema_version": "v1",
            "notes": (
                "Export généré conformément au RGPD art. 15 (droit d'accès) "
                "et art. 20 (portabilité). Les champs sensibles "
                "(password_hash, TOTP secret, recovery codes) sont exclus."
            ),
        },
    }

    user_dict = {k: _serialize(v) for k, v in user_row.items()
                 if k not in ("password_hash", "_session_token")}
    payload["users"] = user_dict

    # — TOTP status only —
    totp_row = await conn.fetchrow(
        "SELECT enrolled_at, last_used_at, recovery_codes_used FROM user_totp WHERE user_id = $1",
        user_id,
    )
    payload["user_totp"] = _serialize(dict(totp_row)) if totp_row else None

    # — user_id-keyed tables —
    payload["xp_log"] = _rows_to_dicts(
        await conn.fetch("SELECT * FROM xp_log WHERE user_id = $1 ORDER BY created_at DESC", user_id)
    )
    payload["streaks"] = _rows_to_dicts(
        await conn.fetch("SELECT * FROM streaks WHERE user_id = $1", user_id)
    )
    payload["user_sessions_history"] = _rows_to_dicts(
        await conn.fetch("SELECT * FROM user_sessions WHERE user_id = $1 ORDER BY started_at DESC", user_id)
    )

    # — eleve_id-keyed tables —
    if eleve_id:
        payload["eleves"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM eleves WHERE id = $1", eleve_id)
        )
        payload["profils_eleves"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM profils_eleves WHERE eleve_id = $1", eleve_id)
        )
        payload["learner_profiles"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM learner_profiles WHERE eleve_id = $1", eleve_id)
        )
        payload["error_log"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM error_log WHERE eleve_id = $1 ORDER BY created_at DESC", eleve_id)
        )
        payload["snapshots_session"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM snapshots_session WHERE eleve_id = $1 ORDER BY created_at DESC", eleve_id)
        )
        payload["consolidation_events"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM consolidation_events WHERE eleve_id = $1 ORDER BY created_at DESC", eleve_id)
        )
        payload["spaced_retrieval_queue"] = _rows_to_dicts(
            await conn.fetch("SELECT * FROM spaced_retrieval_queue WHERE eleve_id = $1", eleve_id)
        )
        payload["onboarding_telemetry_events"] = _rows_to_dicts(
            await conn.fetch(
                "SELECT * FROM onboarding_telemetry_events WHERE eleve_id = $1 ORDER BY created_at DESC",
                eleve_id,
            )
        )
    else:
        for k in (
            "eleves", "profils_eleves", "learner_profiles", "error_log",
            "snapshots_session", "consolidation_events", "spaced_retrieval_queue",
            "onboarding_telemetry_events",
        ):
            payload[k] = []

    # — Dify conversations/messages joined via end_users.session_id == dify_user_id —
    payload["dify_conversations"] = []
    payload["dify_messages"] = []
    if dify_user_id:
        end_users = await conn.fetch(
            "SELECT id FROM end_users WHERE session_id = $1", dify_user_id,
        )
        end_user_ids = [r["id"] for r in end_users]
        if end_user_ids:
            convs = await conn.fetch(
                """SELECT id, app_id, name, summary, mode, status, created_at, updated_at
                   FROM conversations WHERE from_end_user_id = ANY($1::uuid[])
                   ORDER BY created_at DESC""",
                end_user_ids,
            )
            payload["dify_conversations"] = _rows_to_dicts(convs)
            conv_ids = [r["id"] for r in convs]
            if conv_ids:
                msgs = await conn.fetch(
                    """SELECT id, conversation_id, query, answer, message_tokens, answer_tokens,
                              total_price, currency, from_source, created_at
                       FROM messages WHERE conversation_id = ANY($1::uuid[])
                       ORDER BY created_at""",
                    conv_ids,
                )
                payload["dify_messages"] = _rows_to_dicts(msgs)

    return payload


async def delete_user_account(conn: asyncpg.Connection, user_row: dict) -> dict[str, int]:
    """Hard delete cascade. Returns counts per table.

    Order matters : eleve-keyed tables first, then user-keyed, then eleves+users.
    Dify cleanup runs separately (no FK to academie users).
    """
    user_id = user_row["id"]
    eleve_id = user_row.get("eleve_id")
    dify_user_id = user_row.get("dify_user_id")
    counts: dict[str, int] = {}

    def _count(stmt_result: str) -> int:
        try:
            return int(stmt_result.split()[-1])
        except (ValueError, IndexError):
            return 0

    async with conn.transaction():
        # — Dify tables (no FK to academie tables, safe to delete first) —
        if dify_user_id:
            end_user_ids = [
                r["id"] for r in await conn.fetch(
                    "SELECT id FROM end_users WHERE session_id = $1", dify_user_id,
                )
            ]
            if end_user_ids:
                conv_ids = [
                    r["id"] for r in await conn.fetch(
                        "SELECT id FROM conversations WHERE from_end_user_id = ANY($1::uuid[])",
                        end_user_ids,
                    )
                ]
                if conv_ids:
                    counts["dify_messages"] = _count(await conn.execute(
                        "DELETE FROM messages WHERE conversation_id = ANY($1::uuid[])", conv_ids,
                    ))
                    counts["dify_conversations"] = _count(await conn.execute(
                        "DELETE FROM conversations WHERE id = ANY($1::uuid[])", conv_ids,
                    ))
                counts["dify_end_users"] = _count(await conn.execute(
                    "DELETE FROM end_users WHERE id = ANY($1::uuid[])", end_user_ids,
                ))

        # — eleve_id-keyed tables —
        if eleve_id:
            for table in (
                "onboarding_telemetry_events",
                "spaced_retrieval_queue",
                "consolidation_events",
                "snapshots_session",
                "error_log",
                "learner_profiles",
                "profils_eleves",
            ):
                counts[table] = _count(await conn.execute(
                    f"DELETE FROM {table} WHERE eleve_id = $1", eleve_id,
                ))

        # — user_id-keyed tables —
        for table in ("xp_log", "streaks", "user_sessions", "active_sessions", "user_totp"):
            counts[table] = _count(await conn.execute(
                f"DELETE FROM {table} WHERE user_id = $1", user_id,
            ))

        # — Detach FK first then drop eleves + users —
        if eleve_id:
            await conn.execute("UPDATE users SET eleve_id = NULL WHERE id = $1", user_id)
            counts["eleves"] = _count(await conn.execute(
                "DELETE FROM eleves WHERE id = $1", eleve_id,
            ))

        counts["users"] = _count(await conn.execute(
            "DELETE FROM users WHERE id = $1", user_id,
        ))

    return counts
