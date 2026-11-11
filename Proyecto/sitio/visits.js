async function showVisits() {
  if (!/^https?:$/.test(location.protocol)) return;
  try {
    const response = await fetch('/api/visits', { method: 'POST' });
    if (!response.ok) return;
    const { count } = await response.json();
    if (!Number.isSafeInteger(count) || count < 1) return;
    const output = document.getElementById('visits');
    output.textContent = 'Visitas: ' + new Intl.NumberFormat('es-CR').format(count);
    output.hidden = false;
  } catch {
    // The panorama remains usable when the counter is unavailable.
  }
}

showVisits();
