// Dashboard Chart Initializations with Dynamic Multi-Currency Support

document.addEventListener('DOMContentLoaded', () => {
  if (!window.dashboardData || !window.dashboardData.hasData) return;

  const { timeSeries, products } = window.dashboardData;

  // 1. Sales & Volume Trend Chart
  const trendCtx = document.getElementById('salesTrendChart');
  if (trendCtx && timeSeries && timeSeries.labels && timeSeries.labels.length > 0) {
    new Chart(trendCtx, {
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
            tension: 0.25,
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
            tension: 0.25,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                if (context.datasetIndex === 0) {
                  return ' Revenue: ' + formatCurrency(context.parsed.y);
                }
                return ' Units: ' + context.parsed.y.toLocaleString();
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 10 }, maxTicksLimit: 12 }
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            grid: { color: '#f1f5f9' },
            ticks: {
              font: { size: 10 },
              callback: val => formatCurrencyShort(val)
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }

  // 2. Product Category Distribution Chart
  const prodCtx = document.getElementById('productChart');
  if (prodCtx && products && products.length > 0) {
    const prodLabels = products.map(p => p.product);
    const prodSales = products.map(p => p.sales);
    const backgroundColors = [
      '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe',
      '#10b981', '#34d399', '#6ee7b7', '#f59e0b', '#fbbf24'
    ];

    new Chart(prodCtx, {
      type: 'doughnut',
      data: {
        labels: prodLabels,
        datasets: [{
          data: prodSales,
          backgroundColor: backgroundColors.slice(0, prodLabels.length),
          borderWidth: 1.5,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.parsed;
                return ' ' + context.label + ': ' + formatCurrency(val);
              }
            }
          }
        },
        cutout: '65%'
      }
    });
  }
});
