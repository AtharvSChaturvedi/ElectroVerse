// ── CONFIG ────────────────────────────────────────────────────────────────
const API = '';  // same-origin for Flask; change to 'http://localhost:5000' for dev

// ── API HELPER ────────────────────────────────────────────────────────────
async function api(path, method = 'GET', body = null) {
  const opts = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

// ── TOAST ─────────────────────────────────────────────────────────────────
let toastContainer = null;
function toast(msg, type = 'success') {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── AUTH CHECK ────────────────────────────────────────────────────────────
async function requireAuth(role) {
  try {
    const user = await api('/api/auth/me');
    if (user.role !== role) {
      window.location.href = '/';
    }
    return user;
  } catch {
    window.location.href = '/';
  }
}

async function logout() {
  await api('/api/auth/logout', 'POST');
  window.location.href = '/';
}

// ── FORMATTING ────────────────────────────────────────────────────────────
function fmt(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) : '—'; }
function fmtDatetime(d) { return d ? new Date(d).toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'; }

// ── CATEGORY EMOJI ────────────────────────────────────────────────────────
const catEmoji = {
  'Television': '📺', 'Audio': '🎧', 'Smartphones': '📱',
  'Air Conditioners': '❄️', 'Appliances': '🏠', 'Laptops': '💻',
  'Cameras': '📷', 'Gaming': '🎮', 'default': ''
};
function getEmoji(cat) { return catEmoji[cat] || catEmoji['default']; }

// ── MODAL HELPERS ─────────────────────────────────────────────────────────
function showModal(id) { document.getElementById(id).classList.remove('hidden'); }
function hideModal(id) { document.getElementById(id).classList.add('hidden'); }

// ── SIDEBAR RESIZE & COLLAPSE ─────────────────────────────────────────────
function initSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const resizer = document.querySelector('.sidebar-resizer');
  const toggleBtn = document.querySelector('.sidebar-toggle-btn');
  if (!sidebar) return;

  const MIN = 52, MAX = 340, DEFAULT = 215;
  let collapsed = false;

  // Restore saved width
  const saved = localStorage.getItem('sidebar-width');
  if (saved && !collapsed) sidebar.style.width = saved + 'px';

  // ── DRAG RESIZE ──
  if (resizer) {
    let dragging = false, startX = 0, startW = 0;

    resizer.addEventListener('mousedown', e => {
      if (collapsed) return;
      dragging = true;
      startX = e.clientX;
      startW = sidebar.offsetWidth;
      resizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', e => {
      if (!dragging) return;
      const newW = Math.min(MAX, Math.max(MIN, startW + (e.clientX - startX)));
      sidebar.style.width = newW + 'px';
      sidebar.style.transition = 'none';
      if (newW <= MIN + 10) {
        sidebar.classList.add('collapsed');
        collapsed = true;
      } else {
        sidebar.classList.remove('collapsed');
        collapsed = false;
      }
    });

    document.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      resizer.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      sidebar.style.transition = '';
      if (!collapsed) localStorage.setItem('sidebar-width', sidebar.offsetWidth);
    });
  }

  // ── TOGGLE BUTTON ──
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      collapsed = !collapsed;
      if (collapsed) {
        sidebar.classList.add('collapsed');
        sidebar.style.width = MIN + 'px';
        toggleBtn.textContent = '›';
        toggleBtn.title = 'Expand sidebar';
      } else {
        sidebar.classList.remove('collapsed');
        const w = parseInt(localStorage.getItem('sidebar-width')) || DEFAULT;
        sidebar.style.width = w + 'px';
        toggleBtn.textContent = '‹';
        toggleBtn.title = 'Collapse sidebar';
      }
    });
  }
}

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSidebar);
} else {
  initSidebar();
}