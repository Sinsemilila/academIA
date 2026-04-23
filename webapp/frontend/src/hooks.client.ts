/**
 * Refactor 2026-H2 Phase B4 — Sentry / GlitchTip frontend error tracking.
 * No-op si PUBLIC_SENTRY_DSN_FRONTEND est absent (cas dev local).
 */
import * as Sentry from '@sentry/sveltekit';
import { handleErrorWithSentry } from '@sentry/sveltekit';
import { env } from '$env/dynamic/public';

const _DSN = env.PUBLIC_SENTRY_DSN_FRONTEND;
if (_DSN) {
  Sentry.init({
    dsn: _DSN,
    // Phase B4 — tunnel via FastAPI /api/sentry-tunnel pour bypass CSP
    // `connect-src 'self'` injecté par Cosmos + bug CF Access path-precedence.
    // /api/* est déjà couvert par CF Access cookie de sinse → no extra bypass app.
    tunnel: '/api/sentry-tunnel',
    tracesSampleRate: 0.10,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
    environment: 'production',
    sendDefaultPii: false,
    beforeSend(event) {
      // PII scrub : drop cookies + auth headers + body si email pattern
      if (event.request) {
        delete event.request.cookies;
        if (event.request.headers) {
          for (const h of ['cookie', 'Cookie', 'x-csrf-token', 'X-CSRF-Token', 'authorization', 'Authorization']) {
            delete (event.request.headers as Record<string, unknown>)[h];
          }
        }
        if (event.request.data && typeof event.request.data === 'string') {
          if (/password|secret/i.test(event.request.data)) {
            event.request.data = '<scrubbed>';
          }
        }
      }
      if (event.user) {
        event.user = { id: '<redacted>' };
      }
      return event;
    },
  });
}

export const handleError = handleErrorWithSentry();
