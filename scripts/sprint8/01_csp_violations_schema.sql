-- Refactor 2026-H2 Phase A3 — CSP report-only collection.
--
-- Browsers send Content-Security-Policy violation reports to
-- /api/csp-report (un-authed, rate-limited 60r/min/IP) when our
-- Content-Security-Policy-Report-Only header detects a violation.
--
-- 2-week collection in report-only mode → analyse to refine policy
-- → flip to enforce mode.
--
-- Spec : W3C CSP3 reporting (Reporting API + legacy report-uri).
-- Both report formats stored in `raw_report` JSONB to handle either.
--
-- Privacy : we strip query strings from `document_uri` and `blocked_uri`
-- before insert (handled in security_router.py) to avoid PII leak via
-- referrer-like fields. Source IP is hashed (SHA256 + per-day salt).
-- Auto-purge after 90 days via cron.

CREATE TABLE IF NOT EXISTS csp_violations (
  id                  BIGSERIAL PRIMARY KEY,
  reported_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_hash             TEXT,
  user_agent          TEXT,
  document_uri        TEXT,          -- query string stripped
  referrer            TEXT,          -- query string stripped
  violated_directive  TEXT,
  effective_directive TEXT,
  blocked_uri         TEXT,          -- query string stripped
  source_file         TEXT,
  line_number         INTEGER,
  column_number       INTEGER,
  status_code         INTEGER,
  disposition         TEXT,          -- "report" or "enforce"
  raw_report          JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS csp_violations_reported_at_idx
  ON csp_violations (reported_at DESC);

CREATE INDEX IF NOT EXISTS csp_violations_directive_idx
  ON csp_violations (effective_directive, blocked_uri);

-- Aggregation view for analysis dashboard
CREATE OR REPLACE VIEW csp_violations_24h AS
  SELECT effective_directive,
         blocked_uri,
         source_file,
         COUNT(*) AS hits,
         COUNT(DISTINCT ip_hash) AS unique_ips,
         MIN(reported_at) AS first_seen,
         MAX(reported_at) AS last_seen
    FROM csp_violations
   WHERE reported_at > now() - INTERVAL '24 hours'
GROUP BY effective_directive, blocked_uri, source_file
ORDER BY hits DESC;

COMMENT ON TABLE csp_violations IS
  'CSP violations collected during report-only window. See refactor 2026-H2 Phase A3.';
