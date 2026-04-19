"""Unit tests for clone_app.py helpers (no DB access)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_app import _gen_api_key, _gen_site_code, apply_prompts_override, build_clone_sql, SourceApp  # noqa: E402


class TestKeyGen:
    def test_api_key_prefix_and_length(self):
        k = _gen_api_key()
        assert k.startswith("app-")
        # app- + 20 chars = 24
        assert len(k) == 24

    def test_api_key_is_alnum(self):
        k = _gen_api_key()
        assert re.fullmatch(r"app-[A-Za-z0-9]+", k)

    def test_site_code_length_and_charset(self):
        c = _gen_site_code()
        assert len(c) == 14
        assert re.fullmatch(r"[a-z0-9]+", c)


class TestPromptsOverride:
    def test_no_overrides_passthrough(self):
        graph = '{"nodes": [], "edges": []}'
        assert apply_prompts_override(graph, {}) == graph

    def test_simple_substitution(self):
        graph = '{"nodes": [{"data": {"text": "Hello world"}}]}'
        result = apply_prompts_override(graph, {"Hello": "Hola"})
        assert "Hola world" in result
        # still valid JSON
        parsed = json.loads(result)
        assert parsed["nodes"][0]["data"]["text"] == "Hola world"

    def test_substitution_that_breaks_json_raises(self):
        graph = '{"text": "Hello"}'
        with pytest.raises(json.JSONDecodeError):
            # removing the closing quote of the string breaks JSON
            apply_prompts_override(graph, {'"Hello"': '"Hola'})


class TestBuildCloneSql:
    def _fake_source(self, graph: str = '{"nodes":[],"edges":[]}') -> SourceApp:
        return SourceApp(
            app_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000002",
            mode="advanced-chat",
            icon=None, icon_background=None, icon_type=None,
            created_by="00000000-0000-0000-0000-000000000003",
            workflow_id="00000000-0000-0000-0000-000000000004",
            workflow_graph=graph,
            workflow_features='{"file_upload":{}}',
            workflow_type="chat",
            workflow_version="published",
            workflow_env_vars="{}",
            workflow_conv_vars="{}",
            site_code="srccode12345",
            site_default_language="en-US",
        )

    def test_sql_contains_all_4_inserts(self):
        sql = build_clone_sql(
            source=self._fake_source(),
            new_app_id="aaa", new_workflow_id="bbb",
            new_site_id="ccc", new_api_token_id="ddd",
            new_api_key="app-zzzz",
            new_site_code="newcode1234",
            new_name="Maestro",
            new_description="ES tutor",
            new_graph='{"nodes":[]}',
        )
        assert "INSERT INTO workflows" in sql
        assert "INSERT INTO apps" in sql
        assert "INSERT INTO sites" in sql
        assert "INSERT INTO api_tokens" in sql
        # transactional
        assert sql.startswith("BEGIN;")
        assert sql.endswith("COMMIT;")

    def test_sql_escapes_single_quotes(self):
        source = self._fake_source()
        sql = build_clone_sql(
            source=source,
            new_app_id="aaa", new_workflow_id="bbb",
            new_site_id="ccc", new_api_token_id="ddd",
            new_api_key="app-zzzz",
            new_site_code="code",
            new_name="O'Reilly tutor",
            new_description="l'espagnol",
            new_graph='{"x":"y"}',
        )
        # Single quotes doubled
        assert "O''Reilly" in sql
        assert "l''espagnol" in sql
