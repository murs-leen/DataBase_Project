/**
 * HMS – Shared JavaScript Utilities
 * Loaded globally via base.html
 */

// ── Toast Notification ───────────────────────
function showToast(message, type = 'success') {
  const existing = document.getElementById('hms-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'hms-toast';
  toast.textContent = message;
  Object.assign(toast.style, {
    position:     'fixed',
    bottom:       '24px',
    right:        '24px',
    padding:      '12px 20px',
    borderRadius: '10px',
    fontSize:     '13px',
    fontWeight:   '600',
    zIndex:       '9999',
    boxShadow:    '0 8px 32px rgba(0,0,0,0.4)',
    transition:   'opacity 0.4s ease',
    opacity:      '0',
    background:   type === 'success' ? 'rgba(39,201,122,0.9)'
                : type === 'error'   ? 'rgba(240,94,106,0.9)'
                                     : 'rgba(79,125,243,0.9)',
    color: '#fff'
  });

  document.body.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = '1'; });
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}

// ── Confirm Delete Helper ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Auto-highlight active nav based on URL
  const path = window.location.pathname.split('/')[1];
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href') || '';
    if (href.includes(path) && path !== '') {
      item.classList.add('active');
    }
  });

  // Add fade-in to all cards
  document.querySelectorAll('.card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.06}s`;
    card.classList.add('fade-in');
  });
});

// ── Format numbers as PKR ────────────────────
function formatPKR(amount) {
  return 'PKR ' + Number(amount).toLocaleString('en-PK', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  });
}

// ── Table Search (client-side) ───────────────
function initTableSearch(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', () => {
    const term = input.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
    });
  });
}

// ── Auto-refresh badge ───────────────────────
function startRefreshCountdown(seconds, elementId) {
  let remaining = seconds;
  const el = document.getElementById(elementId);
  if (!el) return;
  const interval = setInterval(() => {
    remaining -= 1;
    el.textContent = `Refreshes in ${remaining}s`;
    if (remaining <= 0) {
      remaining = seconds;
    }
  }, 1000);
}

// ── Print helper ─────────────────────────────
function printSection(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const win = window.open('', '_blank');
  win.document.write(`
    <html><head><title>HMS Report</title>
    <style>
      body { font-family: Arial, sans-serif; font-size: 13px; color: #000; }
      table { width:100%; border-collapse:collapse; }
      th, td { border:1px solid #ccc; padding:8px; text-align:left; }
      th { background:#f0f0f0; }
    </style></head><body>
    ${el.innerHTML}
    </body></html>
  `);
  win.document.close();
  win.print();
}
