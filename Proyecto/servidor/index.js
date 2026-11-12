import html from './page.js';

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === '/api/visits') {
      if (request.method !== 'GET' && request.method !== 'POST') {
        return new Response(null, { status: 405, headers: { Allow: 'GET, POST' } });
      }
      const origin = request.headers.get('Origin');
      if (origin && origin !== new URL(request.url).origin) {
        return new Response(null, { status: 403 });
      }
      const { count } = await env.DB.prepare(
        request.method === 'GET'
          ? 'SELECT count FROM visits WHERE id = 1'
          : 'UPDATE visits SET count = count + 1 WHERE id = 1 RETURNING count'
      ).first();
      return Response.json({ count }, { headers: { 'Cache-Control': 'no-store' } });
    }
    if (pathname === '/' || pathname === '/index.html') {
      return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
    }
    return env.ASSETS ? env.ASSETS.fetch(request) : new Response(null, { status: 404 });
  }
};
