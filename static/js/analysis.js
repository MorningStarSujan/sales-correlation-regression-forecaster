// In-depth Analysis & Correlation Matrix Visualizer with Dynamic Multi-Currency Support

document.addEventListener('DOMContentLoaded', () => {
  const { timeSeries } = window.analysisData || {};
  let analysisTrendChart = null;

  // 1. Render Time Series Trend Chart
  const trendCtx = document.getElementById('analysisTrendChart');
  if (trendCtx && timeSeries && timeSeries.labels && timeSeries.labels.length > 0) {
    analysisTrendChart = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: timeSeries.labels,
        datasets: [
          {
            label: 'Sales Revenue (' + getCurrencySymbol() + ')',
            data: timeSeries.sales,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
            borderWidth: 2,
            fill: true,
            tension: 0.2,
            yAxisID: 'y'
          },
          {
            label: 'Units Sold',
            data: timeSeries.units,
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            borderDash: [4, 4],
            pointRadius: 2,
            tension: 0.2,
            yAxisID: 'y1'
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
              label: function(ctx) {
                if (ctx.datasetIndex === 0) {
                  return ' Revenue: ' + formatCurrency(ctx.parsed.y);
                }
                return ' Units: ' + ctx.parsed.y.toLocaleString();
              }
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 12 } },
          y: {
            type: 'linear',
            position: 'left',
            grid: { color: '#f1f5f9' },
            ticks: {
              font: { size: 10 },
              callback: val => formatCurrencyShort(val)
            }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }

  // 2. Color-code Heatmap Cells
  const heatmapCells = document.querySelectorAll('.heatmap-cell');
  heatmapCells.forEach(cell => {
    const r = parseFloat(cell.getAttribute('data-r'));
    if (isNaN(r)) return;

    if (Math.abs(r - 1.0) < 0.001) {
      // Diagonal (1.000)
      cell.style.backgroundColor = '#e2e8f0';
      cell.style.color = '#475569';
      cell.style.fontWeight = '600';
    } else if (r > 0) {
      // Positive correlation: subtle blue gradient
      const alpha = Math.min(0.85, Math.max(0.12, r * 0.85));
      cell.style.backgroundColor = `rgba(37, 99, 235, ${alpha.toFixed(2)})`;
      cell.style.color = alpha > 0.45 ? '#ffffff' : '#0f172a';
    } else {
      // Negative correlation: subtle red/rose gradient
      const absR = Math.abs(r);
      const alpha = Math.min(0.85, Math.max(0.12, absR * 0.85));
      cell.style.backgroundColor = `rgba(220, 38, 38, ${alpha.toFixed(2)})`;
      cell.style.color = alpha > 0.45 ? '#ffffff' : '#0f172a';
    }
  });

  // 3. Currency Selector Management (Dedicated to Data Analysis Page)
  const currencySelector = document.getElementById('currencySelector');

  function updateAnalysisPageCurrency(code) {
    // 1. KPI cards
    const kpiRev = document.getElementById('analysisTotalRevenue');
    if (kpiRev && kpiRev.getAttribute('data-raw-val') !== null) {
      kpiRev.textContent = formatCurrency(kpiRev.getAttribute('data-raw-val'), code);
    }

    const kpiAvg = document.getElementById('analysisAvgSale');
    if (kpiAvg && kpiAvg.getAttribute('data-raw-val') !== null) {
      kpiAvg.textContent = formatCurrency(kpiAvg.getAttribute('data-raw-val'), code);
    }

    const kpiStd = document.getElementById('analysisStdSale');
    if (kpiStd && kpiStd.getAttribute('data-raw-val') !== null) {
      kpiStd.textContent = 'Std Dev: ' + formatCurrency(kpiStd.getAttribute('data-raw-val'), code);
    }

    // 2. Product breakdown table
    const thProductRevenue = document.getElementById('thProductRevenue');
    if (thProductRevenue) {
      thProductRevenue.textContent = `Revenue (${getCurrencySymbol(code)})`;
    }

    document.querySelectorAll('.product-revenue-cell').forEach(cell => {
      const raw = cell.getAttribute('data-raw-val');
      if (raw !== null) {
        cell.textContent = formatCurrency(raw, code);
      }
    });

    // 3. Sales Trend Chart
    if (analysisTrendChart) {
      analysisTrendChart.data.datasets[0].label = 'Sales Revenue (' + getCurrencySymbol(code) + ')';
      analysisTrendChart.update();
    }

    // 4. Export PDF Link sync
    const btnExportPdf = document.getElementById('btnExportPdf');
    if (btnExportPdf) {
      try {
        const u = new URL(btnExportPdf.href, window.location.origin);
        u.searchParams.set('currency', code);
        btnExportPdf.href = u.pathname + u.search;
      } catch (e) {
        // Fallback for relative paths
        const base = btnExportPdf.getAttribute('href').split('?')[0];
        btnExportPdf.setAttribute('href', `${base}?currency=${code}`);
      }
    }
  }

  if (currencySelector) {
    // Sync dropdown with current saved currency
    const activeCode = getCurrentCurrencyCode();
    if (currencySelector.value !== activeCode && window.SUPPORTED_CURRENCIES[activeCode]) {
      currencySelector.value = activeCode;
      updateAnalysisPageCurrency(activeCode);
    }

    currencySelector.addEventListener('change', async () => {
      const selectedCode = currencySelector.value;
      await setCurrentCurrency(selectedCode);
      updateAnalysisPageCurrency(selectedCode);
      showCurrencyToast(`Currency updated to ${selectedCode} (${getCurrencySymbol(selectedCode)})`);
    });
  }

  window.addEventListener('currencyChanged', (e) => {
    if (e.detail && e.detail.currency) {
      if (currencySelector && currencySelector.value !== e.detail.currency) {
        currencySelector.value = e.detail.currency;
      }
      updateAnalysisPageCurrency(e.detail.currency);
    }
  });
});
