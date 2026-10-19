const lot = document.querySelector('.parking-lot');
async function refresh() {
  try {
    const response = await fetch('/api/availability/', {cache:'no-store'});
    if (!response.ok) throw new Error('Unavailable');
    const data = await response.json();
    document.getElementById('free').textContent = data.free;
    document.getElementById('occupied').textContent = data.occupied;
    for (const spot of data.spots) {
      const el = Array.from(lot.querySelectorAll('.spot')).find(el => el.dataset.label === spot.label);
      if (!el) continue;
      const state = spot.label === lot.dataset.own && spot.state === 'occupied' ? 'yours' : spot.state;
      el.className = `spot ${state}`;
      const label = state === 'yours' ? 'Your space' : state === 'occupied' ? 'Occupied' : 'Available';
      el.querySelector('small').textContent = label;
      el.setAttribute('aria-label', `${spot.label}: ${label}`);
    }
    document.getElementById('live').textContent = '● Live availability';
  } catch (_) {document.getElementById('live').textContent = '○ Connection lost · retrying';}
}
setInterval(refresh, 5000);
document.getElementById('checkout')?.addEventListener('submit', event => {
  if (!confirm('Finish your visit? Your exit time and final bill will be recorded now.')) event.preventDefault();
});
document.getElementById('print')?.addEventListener('click', () => window.print());
