// Data Upload, Schema Inspection, and Column Mapping Logic

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const uploadProgress = document.getElementById('uploadProgress');
  const uploadError = document.getElementById('uploadError');
  const validationSection = document.getElementById('validationSection');
  const mappingForm = document.getElementById('mappingForm');

  let currentDatasetId = null;

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUpload(files[0]);
      }
    });

    fileInput.addEventListener('change', e => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });
  }

  async function handleFileUpload(file) {
    uploadError.style.display = 'none';
    uploadProgress.style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      uploadProgress.style.display = 'none';

      if (!data.success) {
        uploadError.textContent = data.error || 'Upload error occurred.';
        uploadError.style.display = 'block';
        return;
      }

      currentDatasetId = data.dataset_id;
      renderValidationData(data);
    } catch (err) {
      uploadProgress.style.display = 'none';
      uploadError.textContent = 'Network or parsing error: ' + err.message;
      uploadError.style.display = 'block';
    }
  }

  function renderValidationData(data) {
    const q = data.quality;
    document.getElementById('valRows').textContent = q.total_rows.toLocaleString();
    document.getElementById('valCols').textContent = q.total_cols;
    document.getElementById('valDups').textContent = q.duplicate_rows.toLocaleString();
    document.getElementById('valDupPct').textContent = `${q.duplicate_pct}% duplicate rows`;

    const integrityVal = document.getElementById('valIntegrity');
    const integritySub = document.getElementById('valIntegritySub');
    if (q.has_missing) {
      integrityVal.textContent = 'Nulls Detected';
      integrityVal.style.color = 'var(--warning)';
      integritySub.textContent = 'Handled gracefully by services';
    } else {
      integrityVal.textContent = 'Clean';
      integrityVal.style.color = 'var(--success)';
      integritySub.textContent = 'Zero missing records';
    }

    // Populate dropdown options
    const cols = data.columns;
    const detected = data.detected_mapping || {};

    populateSelect('mapSalesCol', cols, detected.sales_col, true);
    populateSelect('mapDateCol', cols, detected.date_col, false, '-- None / Non-temporal --');
    populateSelect('mapUnitsCol', cols, detected.units_col, false, '-- None --');
    populateSelect('mapProductCol', cols, detected.product_col, false, '-- None --');

    // Title placeholder
    document.getElementById('analysisTitle').value = `${data.filename.replace(/\.[^/.]+$/, '')} Sales Analysis`;

    // Render Preview Table
    const pHead = document.getElementById('previewHead');
    const pBody = document.getElementById('previewBody');
    pHead.innerHTML = '';
    pBody.innerHTML = '';

    const trH = document.createElement('tr');
    data.preview.headers.forEach(h => {
      const th = document.createElement('th');
      th.textContent = h;
      trH.appendChild(th);
    });
    pHead.appendChild(trH);

    data.preview.rows.forEach(row => {
      const tr = document.createElement('tr');
      row.forEach(val => {
        const td = document.createElement('td');
        td.textContent = val;
        tr.appendChild(td);
      });
      pBody.appendChild(tr);
    });

    validationSection.style.display = 'block';
    validationSection.scrollIntoView({ behavior: 'smooth' });
  }

  function populateSelect(id, columns, selectedVal, isRequired, emptyLabel) {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = '';

    if (!isRequired && emptyLabel) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = emptyLabel;
      sel.appendChild(opt);
    }

    columns.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col;
      opt.textContent = col;
      if (selectedVal && col === selectedVal) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
  }

  // Handle Mapping Confirmation
  if (mappingForm) {
    mappingForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btnConfirmMapping');
      btn.innerHTML = 'Running Automated Calculations...';
      btn.disabled = true;

      const payload = {
        dataset_id: currentDatasetId,
        title: document.getElementById('analysisTitle').value,
        description: document.getElementById('analysisDesc').value,
        column_mapping: {
          sales_col: document.getElementById('mapSalesCol').value,
          date_col: document.getElementById('mapDateCol').value || null,
          units_col: document.getElementById('mapUnitsCol').value || null,
          product_col: document.getElementById('mapProductCol').value || null
        }
      };

      try {
        const res = await fetch('/api/confirm-mapping', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          window.location.href = data.redirect_url;
        } else {
          alert('Error executing analysis: ' + (data.error || 'Unknown error'));
          btn.innerHTML = 'Confirm & Run Automated Analysis &rarr;';
          btn.disabled = false;
        }
      } catch (err) {
        alert('Network error while running analysis: ' + err.message);
        btn.innerHTML = 'Confirm & Run Automated Analysis &rarr;';
        btn.disabled = false;
      }
    });
  }
});
