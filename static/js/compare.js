// History Management & Dataset Comparison Logic

document.addEventListener('DOMContentLoaded', () => {
  // 1. Rename Modal Handling
  const renameModal = document.getElementById('renameModal');
  const renameInput = document.getElementById('renameInput');
  const renameId = document.getElementById('renameId');
  const btnSaveRename = document.getElementById('btnSaveRename');
  const btnCancelRename = document.getElementById('btnCancelRename');

  document.querySelectorAll('.btn-rename').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const title = btn.getAttribute('data-title');
      renameId.value = id;
      renameInput.value = title;
      renameModal.style.display = 'flex';
      renameInput.focus();
    });
  });

  if (btnCancelRename) {
    btnCancelRename.addEventListener('click', () => {
      renameModal.style.display = 'none';
    });
  }

  if (btnSaveRename) {
    btnSaveRename.addEventListener('click', async () => {
      const id = renameId.value;
      const newTitle = renameInput.value.trim();
      if (!newTitle) {
        alert('Analysis title cannot be empty.');
        return;
      }

      btnSaveRename.textContent = 'Saving...';
      btnSaveRename.disabled = true;

      try {
        const res = await fetch(`/api/analyses/${id}/rename`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle })
        });
        const data = await res.json();
        btnSaveRename.textContent = 'Save Title';
        btnSaveRename.disabled = false;

        if (data.success) {
          const titleElem = document.getElementById(`title-text-${id}`);
          if (titleElem) titleElem.textContent = newTitle;
          const btn = document.querySelector(`.btn-rename[data-id="${id}"]`);
          if (btn) btn.setAttribute('data-title', newTitle);
          renameModal.style.display = 'none';
        } else {
          alert('Failed to rename: ' + (data.error || 'Server error'));
        }
      } catch (err) {
        btnSaveRename.textContent = 'Save Title';
        btnSaveRename.disabled = false;
        alert('Network error: ' + err.message);
      }
    });
  }

  // 2. Delete Analysis Handling
  document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      if (!confirm(`Are you sure you want to delete analysis record '${id}'? This action cannot be undone.`)) {
        return;
      }

      try {
        const res = await fetch(`/api/analyses/${id}/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
          const row = document.getElementById(`row-${id}`);
          if (row) row.remove();
        } else {
          alert('Delete error: ' + (data.error || 'Failed to delete'));
        }
      } catch (err) {
        alert('Network error: ' + err.message);
      }
    });
  });

  // 3. Dataset Comparison Engine
  const compareForm = document.getElementById('compareForm');
  if (compareForm) {
    compareForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const idA = document.getElementById('compareIdA').value;
      const idB = document.getElementById('compareIdB').value;

      if (idA === idB) {
        alert('Please select two distinct analyses to compare.');
        return;
      }

      const btn = document.getElementById('btnRunCompare');
      btn.innerHTML = 'Analyzing Differences...';
      btn.disabled = true;

      try {
        const res = await fetch(`/api/compare?id_a=${idA}&id_b=${idB}`);
        const data = await res.json();
        btn.innerHTML = 'Compare Datasets & Analyze Differences &rarr;';
        btn.disabled = false;

        if (!data.success) {
          alert('Comparison error: ' + (data.error || 'Failed to compare'));
          return;
        }

        renderComparisonResults(data.comparison);
      } catch (err) {
        btn.innerHTML = 'Compare Datasets & Analyze Differences &rarr;';
        btn.disabled = false;
        alert('Network error: ' + err.message);
      }
    });
  }

  function renderComparisonResults(comp) {
    // 1. Warnings Banner
    const warnContainer = document.getElementById('compareWarningsContainer');
    warnContainer.innerHTML = '';

    if (comp.warnings && comp.warnings.length > 0) {
      const alertDiv = document.createElement('div');
      alertDiv.className = comp.is_fully_compatible ? 'alert alert-warning' : 'alert alert-danger';
      alertDiv.innerHTML = `
        <div>
          <strong>${comp.is_fully_compatible ? 'Comparability Discrepancies Noted:' : 'Direct Comparability Warning:'}</strong>
          <ul style="margin-top: 6px; padding-left: 20px;">
            ${comp.warnings.map(w => `<li>${w}</li>`).join('')}
          </ul>
        </div>
      `;
      warnContainer.appendChild(alertDiv);
    } else {
      const alertDiv = document.createElement('div');
      alertDiv.className = 'alert alert-success';
      alertDiv.innerHTML = '<div><strong>Compatible Datasets:</strong> Schemas and metrics align cleanly for direct statistical comparison.</div>';
      warnContainer.appendChild(alertDiv);
    }

    // 2. KPI Delta Cards
    const kpiGrid = document.getElementById('compareKpiGrid');
    kpiGrid.innerHTML = '';

    comp.kpis.forEach(k => {
      const card = document.createElement('div');
      card.className = 'kpi-card';

      let valAStr = k.format === 'currency' ? formatCurrency(k.val_a) : formatNumber(k.val_a);
      let valBStr = k.format === 'currency' ? formatCurrency(k.val_b) : formatNumber(k.val_b);
      let diffStr = k.format === 'currency' ? formatCurrency(k.diff) : formatNumber(k.diff);

      const hasPct = k.pct_change !== null && k.pct_change !== undefined;
      const isPositive = k.diff >= 0;
      const pctBadge = hasPct ? `<span class="badge ${isPositive ? 'badge-success' : 'badge-danger'}">${isPositive ? '+' : ''}${k.pct_change}%</span>` : '';

      card.innerHTML = `
        <div class="kpi-label">${k.metric}</div>
        <div style="display: flex; align-items: baseline; gap: 8px; margin: 4px 0;">
          <span style="font-size: 20px; font-weight: 700; color: var(--text-primary);">${valBStr}</span>
          ${pctBadge}
        </div>
        <div class="kpi-subtext">
          Baseline (A): ${valAStr} &bull; Target (B): ${valBStr}
        </div>
        <div style="font-size: 11px; margin-top: 4px; color: ${isPositive ? 'var(--success)' : 'var(--danger)'};">
          Net Delta: ${isPositive ? '+' : ''}${diffStr}
        </div>
      `;
      kpiGrid.appendChild(card);
    });

    // 3. Schema Compatibility Table
    const schemaBody = document.getElementById('compareSchemaBody');
    schemaBody.innerHTML = '';

    const rows = [
      {
        cat: 'Shared Numerical Features',
        fields: comp.shared_cols.length > 0 ? comp.shared_cols.join(', ') : 'None',
        impact: `<span class="badge badge-success">${comp.shared_cols.length} Compatible</span>`
      },
      {
        cat: 'Present only in Dataset A',
        fields: comp.only_in_a.length > 0 ? comp.only_in_a.join(', ') : 'None',
        impact: comp.only_in_a.length > 0 ? `<span class="badge badge-warning">Missing in B</span>` : `<span class="badge badge-neutral">None</span>`
      },
      {
        cat: 'Present only in Dataset B',
        fields: comp.only_in_b.length > 0 ? comp.only_in_b.join(', ') : 'None',
        impact: comp.only_in_b.length > 0 ? `<span class="badge badge-warning">Missing in A</span>` : `<span class="badge badge-neutral">None</span>`
      },
      {
        cat: 'Temporal Intervals',
        fields: `Dataset A: [${comp.dates_a}]<br>Dataset B: [${comp.dates_b}]`,
        impact: comp.dates_a === comp.dates_b ? `<span class="badge badge-success">Matching Spans</span>` : `<span class="badge badge-neutral">Distinct Periods</span>`
      }
    ];

    rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.cat}</strong></td>
        <td>${r.fields}</td>
        <td>${r.impact}</td>
      `;
      schemaBody.appendChild(tr);
    });

    const results = document.getElementById('compareResults');
    results.style.display = 'block';
    results.scrollIntoView({ behavior: 'smooth' });
  }
});
