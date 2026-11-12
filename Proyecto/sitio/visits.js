async function showVisits() {
  if (!/^https?:$/.test(location.protocol)) return;
  try {
    const url = new URL(location.href);
    const excludeThisBrowser = url.searchParams.get('contar') === 'no';
    if (excludeThisBrowser) {
      localStorage.setItem('expo-exclude-visits', 'yes');
      url.searchParams.delete('contar');
      history.replaceState(null, '', url);
    }
    const excluded = localStorage.getItem('expo-exclude-visits') === 'yes';
    const response = await fetch('/api/visits', { method: excluded ? 'GET' : 'POST' });
    if (!response.ok) return;
    const { count } = await response.json();
    if (!Number.isSafeInteger(count) || count < 0) return;
    const output = document.getElementById('visits');
    output.textContent = 'Visitas: ' + new Intl.NumberFormat('es-CR').format(count);
    output.hidden = false;
  } catch {
    // The panorama remains usable when the counter is unavailable.
  }
}

showVisits();
