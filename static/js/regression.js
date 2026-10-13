// Linear Regression Interactive Engine & Chart Rendering

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('regressionForm');
  const targetSelect = document.getElementById('targetVar');
  const testSlider = document.getElementById('testSizeRange');
  const testSizeLabel = document.getElementById('testSizeLabel');
  const trainingSpinner = document.getElementById('trainingSpinner');
  const resultsSection = document.getElementById('modelResultsSection');

  let actualVsPredChartInstance = null;
  let residualChartInstance = null;

  // Sync test size slider label
  if (testSlider && testSizeLabel) {
    testSlider.addEventListener('input', () => {
      testSizeLabel.textContent = `${testSlider.value}%`;
    });
  }

  // Ensure target variable is not selected as a predictor
  if (targetSelect) {
    targetSelect.addEventListener('change', () => {
      const currentTarget = targetSelect.value;
      const checkboxes = document.querySelectorAll('.predictor-check');
      checkboxes.forEach(cb => {
        if (cb.value === currentTarget) {
          cb.checked = false;
          cb.disabled = true;
        } else {
          cb.disabled = false;
        }
      });
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const selectedPredictors = Array.from(document.querySelectorAll('.predictor-check:checked')).map(cb => cb.value);

      if (selectedPredictors.length === 0) {
        alert('Please select at least one predictor variable (independent variable).');
        return;
      }

      trainingSpinner.style.display = 'block';
      resultsSection.style.display = 'none';

      const payload = {
        analysis_id: document.getElementById('analysisId').value,
        target_variable: targetSelect.value,
        predictor_variables: selectedPredictors,
        split_type: document.getElementById('splitType').value,
        test_size: parseFloat(testSlider.value) / 100.0
      };

      try {
        const res = await fetch('/api/regression/train', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        trainingSpinner.style.display = 'none';

        if (!data.success) {
          alert('Model training error: ' + (data.error || 'Failed to fit model'));
          return;
        }

        renderModelResults(data);
      } catch (err) {
        trainingSpinner.style.display = 'none';
        alert('Network error fitting regression model: ' + err.message);
      }
    });
  }

  function renderModelResults(data) {
    // 1. KPI Cards
    document.getElementById('resR2').textContent = parseFloat(data.r2_score).toFixed(4);
    document.getElementById('resFitQuality').textContent = data.fit_quality || 'Variance explained';

    document.getElementById('resMAE').textContent = formatCurrency(data.mae);
    document.getElementById('resRMSE').textContent = formatCurrency(data.rmse);
    document.getElementById('resTrainR2').textContent = parseFloat(data.r2_train || data.r2_score).toFixed(4);

    const diffR2 = Math.abs((data.r2_train || data.r2_score) - data.r2_score);
    const overfitCheck = document.getElementById('resOverfitCheck');
    if (diffR2 > 0.25) {
      overfitCheck.textContent = 'Possible slight overfitting observed';
      overfitCheck.style.color = 'var(--warning)';
    } else {
      overfitCheck.textContent = 'Stable generalizability';
      overfitCheck.style.color = 'var(--success)';
    }

    // 2. Equation
    document.getElementById('resEquation').textContent = data.equation;

    // 3. Coefficients Table
    const tbody = document.getElementById('coefficientsBody');
    tbody.innerHTML = '';

    // Intercept Row
    const trInt = document.createElement('tr');
    trInt.innerHTML = `
      <td><strong>Intercept (β₀)</strong></td>
      <td><span class="badge badge-neutral">Baseline Constant</span></td>
      <td><strong>${data.intercept > 0 ? '+' : ''}${parseFloat(data.intercept).toFixed(4)}</strong></td>
      <td style="color: var(--text-secondary);">Estimated baseline level when all predictor values are zero.</td>
    `;
    tbody.appendChild(trInt);

    // Predictor Rows
    for (const [feat, coef] of Object.entries(data.coefficients)) {
      const tr = document.createElement('tr');
      const numCoef = parseFloat(coef);
      const isPositive = numCoef > 0;
      tr.innerHTML = `
        <td><strong>${feat}</strong></td>
        <td><span class="badge badge-primary">Explanatory Feature</span></td>
        <td><strong style="color: ${isPositive ? 'var(--primary)' : 'var(--danger)'};">${isPositive ? '+' : ''}${numCoef.toFixed(4)}</strong></td>
        <td style="color: var(--text-secondary);">
          Each 1-unit increase in '${feat}' ${isPositive ? 'increases' : 'decreases'} predicted ${data.target_variable} by ${Math.abs(numCoef).toFixed(4)}.
        </td>
      `;
      tbody.appendChild(tr);
    }

    // 4. Actual vs Predicted Chart
    renderActualVsPredictedChart(data.comparison_points);

    // 5. Residual Chart
    renderResidualChart(data.comparison_points);

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  function renderActualVsPredictedChart(points) {
    const ctx = document.getElementById('actualVsPredChart');
    if (!ctx || !points) return;

    if (actualVsPredChartInstance) {
      actualVsPredChartInstance.destroy();
    }

    const labels = points.map(p => p.label);
    const actuals = points.map(p => p.actual);
    const predicteds = points.map(p => p.predicted);

    actualVsPredChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual Observed',
            data: actuals,
            borderColor: '#0f172a',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            pointRadius: 2,
            tension: 0.1
          },
          {
            label: 'Predicted Model Fit',
            data: predicteds,
            borderColor: '#2563eb',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 4],
            pointRadius: 0,
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 12 } },
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

  function renderResidualChart(points) {
    const ctx = document.getElementById('residualChart');
    if (!ctx || !points) return;

    if (residualChartInstance) {
      residualChartInstance.destroy();
    }

    const labels = points.map(p => p.label);
    const residuals = points.map(p => p.residual);
    const barColors = residuals.map(r => r >= 0 ? 'rgba(37, 99, 235, 0.65)' : 'rgba(220, 38, 38, 0.65)');

    residualChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Residual Error (y - ŷ)',
          data: residuals,
          backgroundColor: barColors,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` Error: ${formatCurrency(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          x: { display: false },
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

  // If a previously trained model exists, render it immediately
  if (window.existingModels && window.existingModels.length > 0) {
    const latest = window.existingModels[0];
    renderModelResults({
      target_variable: latest.target_variable,
      predictor_variables: latest.predictor_variables,
      r2_score: latest.r2_score,
      mae: latest.mae,
      rmse: latest.rmse,
      coefficients: latest.coefficients,
      intercept: latest.intercept,
      comparison_points: latest.actual_vs_predicted,
      equation: `Estimated ${latest.target_variable} = ${latest.intercept > 0 ? '+' : ''}${latest.intercept.toFixed(4)} ` +
        Object.entries(latest.coefficients).map(([k, v]) => `${v >= 0 ? '+' : ''}${parseFloat(v).toFixed(4)} × [${k}]`).join(' '),
      fit_quality: latest.r2_score >= 0.8 ? 'High explanatory power' : (latest.r2_score >= 0.5 ? 'Moderate explanatory power' : 'Weak explanatory power')
    });
  }
});
