import type { Handle } from '@sveltejs/kit';

const API_BACKEND = process.env.API_BACKEND || 'http://academie-api:8000';

export const handle: Handle = async ({ event, resolve }) => {
  // Proxy /api/* requests to FastAPI backend
  if (event.url.pathname.startsWith('/api/')) {
    const targetUrl = `${API_BACKEND}${event.url.pathname}${event.url.search}`;

    const headers = new Headers();
    for (const [key, value] of event.request.headers) {
      if (['content-type', 'authorization', 'accept'].includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    }

    let body: BodyInit | undefined;
    if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
      body = await event.request.arrayBuffer();
    }

    const response = await fetch(targetUrl, {
      method: event.request.method,
      headers,
      body,
    });

    // For SSE streams, pass through the body directly
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  return resolve(event);
};
