import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import * as Sentry from '@sentry/sveltekit';
import { sentryHandle, handleErrorWithSentry } from '@sentry/sveltekit';
import { env } from '$env/dynamic/private';

const API_BACKEND = process.env.API_BACKEND || 'http://academie-api:8000';

// Phase B4 — Sentry / GlitchTip SSR error tracking. Conditional on env DSN
// (no-op in dev). Reuses the frontend DSN so SSR + client errors both land
// in the `academie-frontend` project ; if you want them separated, set
// SENTRY_DSN_SSR distinctly.
const _SSR_DSN = env.SENTRY_DSN_SSR || env.PUBLIC_SENTRY_DSN_FRONTEND;
if (_SSR_DSN) {
  Sentry.init({
    dsn: _SSR_DSN,
    tracesSampleRate: 0.10,
    sendDefaultPii: false,
    environment: 'production',
  });
}

// Refactor 2026-H2 Phase A3 — CSP Report-Only.
// Initial directives are intentionally permissive (still allowing
// 'unsafe-inline' for script/style) to capture the baseline of what
// SvelteKit + Dify + LLM endpoints actually load. After 2 weeks of
// collection at /api/csp-report, we tighten and flip to enforce mode.
const CSP_REPORT_ONLY_DIRECTIVES = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' https://academie.petit-pont.com https://dify.petit-pont.com https://glitchtip.petit-pont.com wss://academie.petit-pont.com",
  "frame-src 'self' https://dify.petit-pont.com https://challenges.cloudflare.com",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "report-uri /api/csp-report",
].join('; ');

const customHandle: Handle = async ({ event, resolve }) => {
  // Proxy /api/* requests to FastAPI backend (no CSP — JSON/streams)
  if (event.url.pathname.startsWith('/api/')) {
    const targetUrl = `${API_BACKEND}${event.url.pathname}${event.url.search}`;

    const headers = new Headers();
    // Phase A1 — forward `cookie` (session+csrf) and `x-csrf-token` from
    // browser to FastAPI. `authorization` kept for legacy compat (post-A1
    // cleanup will remove it once no clients send Bearer).
    const ALLOWED_REQ = new Set([
      'content-type', 'authorization', 'accept', 'cookie', 'x-csrf-token',
    ]);
    for (const [key, value] of event.request.headers) {
      if (ALLOWED_REQ.has(key.toLowerCase())) {
        headers.set(key, value);
      }
    }
    // Forward original client IP for rate limiting + CSP-report IP hashing
    const xff = event.request.headers.get('x-forwarded-for') ||
                event.getClientAddress();
    if (xff) headers.set('x-forwarded-for', xff);

    let body: BodyInit | undefined;
    if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
      body = await event.request.arrayBuffer();
    }

    const response = await fetch(targetUrl, {
      method: event.request.method,
      headers,
      body,
    });

    // Phase A1 — explicitly forward each Set-Cookie value (Node 20+ getSetCookie).
    // Avoids accidental consolidation of multiple Set-Cookie into a single
    // comma-joined header (which browsers reject).
    const proxiedHeaders = new Headers(response.headers);
    proxiedHeaders.delete('set-cookie');
    for (const cookie of response.headers.getSetCookie?.() ?? []) {
      proxiedHeaders.append('set-cookie', cookie);
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: proxiedHeaders,
    });
  }

  // SvelteKit-rendered HTML pages — apply CSP report-only + COOP/COEP
  const response = await resolve(event);

  response.headers.set('Content-Security-Policy-Report-Only', CSP_REPORT_ONLY_DIRECTIVES);
  response.headers.set('Cross-Origin-Opener-Policy', 'same-origin');
  response.headers.set('Cross-Origin-Resource-Policy', 'same-origin');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
};

// Phase B4 — sequence sentryHandle wrapper before our custom handle so any
// thrown error in the proxy or page resolution is captured.
export const handle = _SSR_DSN ? sequence(sentryHandle(), customHandle) : customHandle;
export const handleError = handleErrorWithSentry();
