// Sortable tables
(function () {
  const SKIP_CLASSES = ['section-divider-row', 'section-label-row', 'section-header-repeat'];

  function rawVal(td) {
    if (!td) return '';
    const v = td.dataset.val;
    if (v !== undefined) return isNaN(v) ? v.toLowerCase() : parseFloat(v);
    const text = td.textContent.trim();
    // parse Argentine format: remove dots (thousands), replace comma with dot (decimal)
    const cleaned = text.replace(/\./g, '').replace(',', '.').replace(/[^0-9.\-+]/g, '');
    const n = parseFloat(cleaned);
    return isNaN(n) ? text.toLowerCase() : n;
  }

  function sortTable(tbody, colIdx, asc) {
    const rows = Array.from(tbody.rows).filter(r => !SKIP_CLASSES.some(c => r.classList.contains(c)));
    rows.sort((a, b) => {
      const av = rawVal(a.cells[colIdx]);
      const bv = rawVal(b.cells[colIdx]);
      if (typeof av === 'number' && typeof bv === 'number') return asc ? av - bv : bv - av;
      return asc ? String(av).localeCompare(String(bv), 'es') : String(bv).localeCompare(String(av), 'es');
    });
    rows.forEach(r => tbody.appendChild(r));
  }

  function initTable(table) {
    const tbody = table.tBodies[0];
    if (!tbody) return;
    let sortCol = null, sortAsc = true;

    table.querySelectorAll('thead th[data-sort]').forEach(th => {
      th.style.cursor = 'pointer';
      th.style.userSelect = 'none';
      const icon = document.createElement('span');
      icon.className = 'sort-icon';
      icon.textContent = ' ⇅';
      th.appendChild(icon);

      th.addEventListener('click', () => {
        const col = parseInt(th.dataset.sort);
        sortAsc = sortCol === col ? !sortAsc : true;
        sortCol = col;
        table.querySelectorAll('.sort-icon').forEach(i => { i.textContent = ' ⇅'; i.style.opacity = '0.35'; });
        icon.textContent = sortAsc ? ' ↑' : ' ↓';
        icon.style.opacity = '1';
        sortTable(tbody, col, sortAsc);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('table[data-sortable]').forEach(initTable);
  });
  // Re-init after HTMX swaps
  document.addEventListener('htmx:afterSwap', () => {
    document.querySelectorAll('table[data-sortable]').forEach(initTable);
  });
})();
