// Forecasting Interactive Engine (Scenario What-If & Multi-Period Horizon)

document.addEventListener('DOMContentLoaded', () => {
  const { analysisId, models, descriptiveStats } = window.forecastConfig || {};
  if (!models || models.length === 0) return;

  const modelSelect = document.getElementById('modelSelect');
  const scenarioInputsContainer = document.getElementById('scenarioInputsContainer');
  const scenarioForm = document.getElementById('scenarioForm');
  const horizonForm = document.getElementById('horizonForm');
  const growthSlider = document.getElementById('growthRatePct');
  const growthLabel = document.getElementById('growthRateLabel');

  let horizonChartInstance = null;
  let activeModel = models[0];

  // Tab switching
  const tabButtons = document.querySelectorAll('.mode-tab');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => {
        b.classList.remove('active', 'btn-primary');
        b.classList.add('btn-secondary');
      });
      btn.classList.add('active', 'btn-primary');
      btn.classList.remove('btn-secondary');

      const targetTabId = btn.getAttribute('data-tab');
      document.querySelectorAll('.forecast-tab-content').forEach(content => {
        content.style.display = content.id === targetTabId ? 'block' : 'none';
      });
    });
  });

  // Slider label sync
  if (growthSlider && growthLabel) {
    growthSlider.addEventListener('input', () => {
      const val = parseFloat(growthSlider.value);
      growthLabel.textContent = `${val > 0 ? '+' : ''}${val.toFixed(1)}%`;
    });
  }

  // Model selection change
  if (modelSelect) {
    modelSelect.addEventListener('change', () => {
      activeModel = models.find(m => m.id === modelSelect.value) || models[0];
      updateActiveModelHeader();
      buildScenarioInputs();
    });
  }

  function updateActiveModelHeader() {
    document.getElementById('sumTarget').textContent = activeModel.target_variable;
    document.getElementById('sumR2').textContent = parseFloat(activeModel.r2_score).toFixed(4);
    document.getElementById('sumRMSE').textContent = formatCurrency(activeModel.rmse);
    document.getElementById('sumPredictors').textContent = activeModel.predictor_variables.join(', ');
  }

  function buildScenarioInputs() {
    if (!scenarioInputsContainer) return;
    scenarioInputsContainer.innerHTML = '';

    activeModel.predictor_variables.forEach(feat => {
      const stats = descriptiveStats[feat] || {};
      const meanVal = stats.mean !== undefined ? stats.mean : 100;
      const minVal = stats.min !== undefined ? stats.min : 0;
      const maxVal = stats.max !== undefined ? stats.max : 1000;

      const group = document.createElement('div');
      group.className = 'form-group';
      group.innerHTML = `
        <label class="form-label" for="inp_${feat}">
          ${feat}
        </label>
        <input type="number" step="any" id="inp_${feat}" class="form-control scenario-inp" data-feature="${feat}" value="${meanVal}" required>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">
          Observed Range: ${minVal} &ndash; ${maxVal} (Avg: ${meanVal})
        </div>
      `;
      scenarioInputsContainer.appendChild(group);
    });
  }

  // Initial build
  updateActiveModelHeader();
  buildScenarioInputs();

  // Handle Scenario Forecast Submission
  if (scenarioForm) {
    scenarioForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btnCalculateScenario');
      btn.innerHTML = 'Calculating...';
      btn.disabled = true;

      const inputs = {};
      document.querySelectorAll('.scenario-inp').forEach(inp => {
        const feat = inp.getAttribute('data-feature');
        inputs[feat] = parseFloat(inp.value);
      });

      try {
        const res = await fetch('/api/forecast/scenario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model_id: activeModel.id,
            analysis_id: analysisId,
            inputs: inputs
          })
        });
        const data = await res.json();
        btn.innerHTML = 'Calculate Scenario Forecast';
        btn.disabled = false;

        if (!data.success) {
          alert('Forecast calculation error: ' + (data.error || 'Unknown error'));
          return;
        }

        renderScenarioResults(data);
      } catch (err) {
        btn.innerHTML = 'Calculate Scenario Forecast';
        btn.disabled = false;
        alert('Network error calculating scenario: ' + err.message);
      }
    });
  }

  function renderScenarioResults(data) {
    document.getElementById('scenPredicted').textContent = formatCurrency(data.predicted_value);
    document.getElementById('scenBounds').textContent = `${formatCurrency(data.lower_bound_95)} – ${formatCurrency(data.upper_bound_95)}`;
    document.getElementById('scenMargin').textContent = `± ${formatCurrency(data.margin_error)}`;

    // Extrapolation warnings
    const notice = document.getElementById('extrapolationNotice');
    if (data.extrapolation_warnings && data.extrapolation_warnings.length > 0) {
      notice.innerHTML = `<strong>Extrapolation Notice:</strong><br>${data.extrapolation_warnings.join('<br>')}`;
      notice.style.display = 'block';
    } else {
      notice.style.display = 'none';
    }

    // Factor breakdown
    const tbody = document.getElementById('scenContribBody');
    tbody.innerHTML = '';

    // Intercept Row
    const trInt = document.createElement('tr');
    trInt.innerHTML = `
      <td><strong>Baseline Constant (Intercept)</strong></td>
      <td>&mdash;</td>
      <td>${data.intercept > 0 ? '+' : ''}${parseFloat(data.intercept).toFixed(4)}</td>
      <td><strong>${formatCurrency(data.intercept)}</strong></td>
    `;
    tbody.appendChild(trInt);

    data.factor_breakdown.forEach(f => {
      const tr = document.createElement('tr');
      const isPos = f.contribution >= 0;
      tr.innerHTML = `
        <td><strong>${f.feature}</strong></td>
        <td>${f.input_value.toLocaleString()}</td>
        <td>${f.coefficient > 0 ? '+' : ''}${parseFloat(f.coefficient).toFixed(4)}</td>
        <td style="color: ${isPos ? 'var(--primary)' : 'var(--danger)'};">
          <strong>${isPos ? '+' : ''}${formatCurrency(f.contribution)}</strong>
        </td>
      `;
      tbody.appendChild(tr);
    });

    const resultBox = document.getElementById('scenarioResultBox');
    resultBox.style.display = 'block';
    resultBox.scrollIntoView({ behavior: 'smooth' });
  }

  // Handle Horizon Forecast Submission
  if (horizonForm) {
    horizonForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btnCalculateHorizon');
      btn.innerHTML = 'Projecting...';
      btn.disabled = true;

      const periods = parseInt(document.getElementById('horizonPeriods').value);
      const growth = parseFloat(document.getElementById('growthRatePct').value);

      try {
        const res = await fetch('/api/forecast/horizon', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model_id: activeModel.id,
            analysis_id: analysisId,
            periods: periods,
            growth_rate_pct: growth
          })
        });
        const data = await res.json();
        btn.innerHTML = 'Generate Horizon Projection';
        btn.disabled = false;

        if (!data.success) {
          alert('Projection error: ' + (data.error || 'Failed to project horizon'));
          return;
        }

        renderHorizonResults(data);
      } catch (err) {
        btn.innerHTML = 'Generate Horizon Projection';
        btn.disabled = false;
        alert('Network error projecting horizon: ' + err.message);
      }
    });
  }

  function renderHorizonResults(data) {
    const tableBody = document.getElementById('horizonBody');
    tableBody.innerHTML = '';

    const labels = [];
    const forecastVals = [];
    const lowerBounds = [];
    const upperBounds = [];

    data.results.forEach(r => {
      labels.push(r.period);
      forecastVals.push(r.predicted_sales);
      lowerBounds.push(r.lower_bound_95);
      upperBounds.push(r.upper_bound_95);

      const tr = document.createElement('tr');
      const predSummary = Object.entries(r.predictor_inputs).map(([k, v]) => `${k}: ${v}`).join('; ');
      tr.innerHTML = `
        <td><strong>${r.period}</strong></td>
        <td><strong style="color: var(--primary);">${formatCurrency(r.predicted_sales)}</strong></td>
        <td style="color: var(--text-secondary);">${formatCurrency(r.lower_bound_95)}</td>
        <td style="color: var(--text-secondary);">${formatCurrency(r.upper_bound_95)}</td>
        <td style="font-size: 11px; color: var(--text-muted);">${predSummary}</td>
      `;
      tableBody.appendChild(tr);
    });

    // Render Chart
    const ctx = document.getElementById('horizonChart');
    if (ctx) {
      if (horizonChartInstance) {
        horizonChartInstance.destroy();
      }

      horizonChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Upper 95% Bound',
              data: upperBounds,
              borderColor: 'transparent',
              backgroundColor: 'rgba(37, 99, 235, 0.12)',
              fill: '+1',
              pointRadius: 0
            },
            {
              label: 'Lower 95% Bound',
              data: lowerBounds,
              borderColor: 'transparent',
              backgroundColor: 'transparent',
              pointRadius: 0
            },
            {
              label: 'Forecasted Sales (' + getCurrencySymbol() + ')',
              data: forecastVals,
              borderColor: '#2563eb',
              backgroundColor: 'transparent',
              borderWidth: 2.5,
              pointRadius: 4,
              pointBackgroundColor: '#2563eb',
              tension: 0.2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                filter: item => item.text.startsWith('Forecasted Sales') || item.text === 'Upper 95% Bound',
                boxWidth: 12,
                font: { size: 11 }
              }
            },
            tooltip: {
              callbacks: {
                label: ctx => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`
              }
            }
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 10 } } },
            y: {
              grid: { color: '#f1f5f9' },
              ticks: {
                font: { size: 10 },
                callback: v => formatCurrencyShort(v)
              }
            }
          }
        }
      });
    }

    const box = document.getElementById('horizonResultBox');
    box.style.display = 'block';
    box.scrollIntoView({ behavior: 'smooth' });
  }
});
