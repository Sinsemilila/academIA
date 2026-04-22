import type { Handle } from '@sveltejs/kit';

const API_BACKEND = process.env.API_BACKEND || 'http://academie-api:8000';

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
  "connect-src 'self' https://academie.petit-pont.com https://dify.petit-pont.com wss://academie.petit-pont.com",
  "frame-src 'self' https://dify.petit-pont.com https://challenges.cloudflare.com",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "report-uri /api/csp-report",
].join('; ');

export const handle: Handle = async ({ event, resolve }) => {
  // Proxy /api/* requests to FastAPI backend (no CSP — JSON/streams)
  if (event.url.pathname.startsWith('/api/')) {
    const targetUrl = `${API_BACKEND}${event.url.pathname}${event.url.search}`;

    const headers = new Headers();
    for (const [key, value] of event.request.headers) {
      if (['content-type', 'authorization', 'accept'].includes(key.toLowerCase())) {
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

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
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
