/**
 * Phase B4 — Sentry tunnel proxy.
 *
 * Bypass le CSP `connect-src 'self'` injecté par Cosmos sur academie.petit-pont.com.
 * Le SDK Sentry frontend POST sur même origine `/sentry-tunnel`, on forward vers
 * GlitchTip server-side (pas de CSP browser-side, juste réseau docker interne).
 *
 * Doc Sentry : https://docs.sentry.io/platforms/javascript/troubleshooting/#dealing-with-ad-blockers
 */
import type { RequestHandler } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

const GLITCHTIP_INTERNAL = env.SENTRY_DSN_BACKEND
  ? new URL(env.SENTRY_DSN_BACKEND).origin
  : 'http://glitchtip-web:8000';

export const POST: RequestHandler = async ({ request }) => {
  // Sentry envelope = NDJSON; first line = envelope header containing dsn URL
  const body = await request.arrayBuffer();
  const text = new TextDecoder().decode(body);
  const firstLine = text.split('\n', 1)[0];
  let projectId: string | null = null;
  try {
    const header = JSON.parse(firstLine);
    if (header.dsn) {
      projectId = new URL(header.dsn).pathname.replace(/^\//, '');
    }
  } catch {
    // ignore
  }
  if (!projectId) {
    return new Response('missing project id', { status: 400 });
  }

  const target = `${GLITCHTIP_INTERNAL}/api/${projectId}/envelope/`;
  const upstream = await fetch(target, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-sentry-envelope' },
    body,
  });

  return new Response(null, { status: upstream.status });
};
