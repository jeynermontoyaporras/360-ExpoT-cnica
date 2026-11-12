import html from './page.js';

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === '/api/visits/locations') {
      if (request.method !== 'GET') {
        return new Response(null, { status: 405, headers: { Allow: 'GET' } });
      }
      const [total, locations] = await env.DB.batch([
        env.DB.prepare('SELECT count FROM visits WHERE id = 1'),
        env.DB.prepare('SELECT country, region, count FROM visit_locations ORDER BY count DESC, country, region')
      ]);
      const recorded = locations.results.reduce((sum, location) => sum + location.count, 0);
      return Response.json({
        total: total.results[0].count,
        beforeLocationTracking: total.results[0].count - recorded,
        locations: locations.results
      }, { headers: { 'Cache-Control': 'no-store' } });
    }
    if (pathname === '/api/visits') {
      if (request.method !== 'GET' && request.method !== 'POST') {
        return new Response(null, { status: 405, headers: { Allow: 'GET, POST' } });
      }
      const origin = request.headers.get('Origin');
      if (origin && origin !== new URL(request.url).origin) {
        return new Response(null, { status: 403 });
      }
      const excluded = (request.headers.get('Cookie') ?? '').split(';')
        .some(cookie => cookie.trim() === 'expo-exclude-visits=yes');
      if (request.method === 'GET' || excluded) {
        const total = await env.DB.prepare('SELECT count FROM visits WHERE id = 1').first();
        return Response.json(total, { headers: { 'Cache-Control': 'no-store' } });
      }
      const countryCode = request.cf?.country;
      const country = /^[A-Z]{2}$/.test(countryCode ?? '') && !['XX', 'T1'].includes(countryCode)
        ? countryCode : '';
      const region = country && typeof request.cf?.region === 'string'
        ? request.cf.region.trim().slice(0, 120) : '';
      const [total] = await env.DB.batch([
        env.DB.prepare('UPDATE visits SET count = count + 1 WHERE id = 1 RETURNING count'),
        env.DB.prepare(`INSERT INTO visit_locations (country, region, count) VALUES (?, ?, 1)
          ON CONFLICT(country, region) DO UPDATE SET count = count + 1`).bind(country, region)
      ]);
      const { count } = total.results[0];
      return Response.json({ count }, { headers: { 'Cache-Control': 'no-store' } });
    }
    if (pathname === '/' || pathname === '/index.html') {
      const headers = new Headers({ 'Content-Type': 'text/html; charset=utf-8' });
      if (new URL(request.url).searchParams.get('contar') === 'no') {
        headers.set('Set-Cookie', 'expo-exclude-visits=yes; Path=/; Max-Age=31536000; Secure; HttpOnly; SameSite=Lax');
        headers.set('Cache-Control', 'no-store');
      }
      return new Response(html, { headers });
    }
    return env.ASSETS ? env.ASSETS.fetch(request) : new Response(null, { status: 404 });
  }
};
