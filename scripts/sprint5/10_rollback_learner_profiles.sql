-- Sprint 5 Phase 5 — Rollback learner_profiles
-- ATTENTION : destructif, supprime toutes les données QCM. À utiliser en dernier recours.
-- Rollback safe = laisser la table vide (ENABLE_QCM_ONBOARDING=false + flag frontend).

BEGIN;

DROP TRIGGER IF EXISTS learner_profiles_updated_at ON learner_profiles;
DROP FUNCTION IF EXISTS trg_learner_profiles_updated_at();
DROP TABLE IF EXISTS learner_profiles;

-- ENUMs : gardés par défaut (peuvent être réutilisés).
-- Si vraiment tout nettoyer :
-- DROP TYPE IF EXISTS fla_category_enum;
-- DROP TYPE IF EXISTS cefr_enum;
-- DROP TYPE IF EXISTS engagement_enum;
-- DROP TYPE IF EXISTS autonomy_enum;
-- DROP TYPE IF EXISTS mindset_enum;

COMMIT;
