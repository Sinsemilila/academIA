-- Sprint 5 Phase 5 — Onboarding QCM refonte : table learner_profiles
--
-- Design doc : docs/00-project/onboarding-research-2026-04-20/vague2-qcm-design.md §6
-- Plan       : /root/.claude/plans/atomic-beaming-alpaca.md
--
-- Nouvelle table `learner_profiles` pour stocker les résultats du QCM pre-chat.
-- Ne modifie PAS profils_eleves (D3 : séparation des responsabilités, profils_eleves
-- garde niveau observationnel + scores_confiance, learner_profiles = déclaratif QCM).
--
-- Transactionnel + idempotent (re-exécutable sans erreur).
-- Rollback : 10_rollback_learner_profiles.sql

BEGIN;

-- ───────────────────────────────────────────────────────────────────────
-- PART 1 — ENUM types (idempotent via DO block)
-- ───────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mindset_enum') THEN
    CREATE TYPE mindset_enum AS ENUM ('fixed', 'growth');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'autonomy_enum') THEN
    CREATE TYPE autonomy_enum AS ENUM ('guided', 'semi_autonomous', 'autonomous');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'engagement_enum') THEN
    CREATE TYPE engagement_enum AS ENUM ('daily_short', 'weekly_long', 'opportunistic', 'daily_intense');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cefr_enum') THEN
    CREATE TYPE cefr_enum AS ENUM ('A1','A2','B1','B2','C1','C2');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fla_category_enum') THEN
    CREATE TYPE fla_category_enum AS ENUM ('low', 'moderate', 'high');
  END IF;
END$$;

-- ───────────────────────────────────────────────────────────────────────
-- PART 2 — Table learner_profiles
-- ───────────────────────────────────────────────────────────────────────
--
-- Schéma JSONB-heavy pour évolutivité cross-domain (Bloc A identique,
-- Bloc B+C varient par domaine). Les contraintes fines sont assurées
-- au niveau applicatif (Pydantic) + via le JSON Schema (data/onboarding/schema.json).

CREATE TABLE IF NOT EXISTS learner_profiles (
  id                   BIGSERIAL PRIMARY KEY,
  eleve_id             BIGINT NOT NULL REFERENCES eleves(id) ON DELETE CASCADE,
  domain               VARCHAR(16) NOT NULL,                         -- "en", "es", "it", "pymentor" …
  target_language      VARCHAR(8),                                    -- ISO-639-1, NULL pour domaines non-langue
  universal_block      JSONB NOT NULL,                                -- Bloc A (self_efficacy, mindset, goal_text, goal_specificity_score, autonomy_pref, engagement_pattern)
  domain_level         JSONB NOT NULL,                                -- Bloc B (cefr_comprehension, cefr_production, probe_answer, probe_score, probe_flag, cefr_baseline, cefr_final, cefr_placement)
  domain_motivation    JSONB NOT NULL,                                -- Bloc C (ideal_l2_self_tags, fla_items_raw, fla_score, fla_category)
  derived_tutor_hints  JSONB,                                         -- Dérivés calculés au POST : scaffolding_level, feedback_framing, session_length_target, …
  schema_version       VARCHAR(8) NOT NULL DEFAULT 'v1',
  completed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT learner_profiles_unique_per_target
    UNIQUE (eleve_id, domain, target_language)
);

-- ───────────────────────────────────────────────────────────────────────
-- PART 3 — Indexes
-- ───────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_learner_profiles_eleve_domain
  ON learner_profiles (eleve_id, domain);

CREATE INDEX IF NOT EXISTS idx_learner_profiles_completed_at
  ON learner_profiles (completed_at DESC);

-- ───────────────────────────────────────────────────────────────────────
-- PART 4 — Trigger updated_at auto
-- ───────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION trg_learner_profiles_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS learner_profiles_updated_at ON learner_profiles;
CREATE TRIGGER learner_profiles_updated_at
  BEFORE UPDATE ON learner_profiles
  FOR EACH ROW EXECUTE FUNCTION trg_learner_profiles_updated_at();

-- ───────────────────────────────────────────────────────────────────────
-- PART 5 — Verify
-- ───────────────────────────────────────────────────────────────────────

DO $$
DECLARE
  table_exists BOOLEAN;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'learner_profiles'
  ) INTO table_exists;
  IF NOT table_exists THEN
    RAISE EXCEPTION 'learner_profiles table was not created';
  END IF;
  RAISE NOTICE 'learner_profiles migration OK';
END$$;

COMMIT;
