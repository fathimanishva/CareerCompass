// Chart.js Visualizations for CareerCompass

function renderSkillRadarChart(canvasId, chartData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !chartData || !chartData.labels || chartData.labels.length === 0) return;

  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.1)';
  const labelColor = isDark ? '#cbd5e1' : '#475569';

  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Your Current Proficiency (%)',
          data: chartData.user_scores,
          backgroundColor: 'rgba(37, 99, 235, 0.35)',
          borderColor: '#2563eb',
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#2563eb',
          borderWidth: 2,
          fill: true
        },
        {
          label: 'Target Career Benchmark',
          data: chartData.benchmark_scores,
          backgroundColor: 'rgba(6, 182, 212, 0.15)',
          borderColor: 'rgba(6, 182, 212, 0.8)',
          pointBackgroundColor: '#06b6d4',
          pointBorderColor: '#fff',
          borderDash: [4, 4],
          borderWidth: 1.5,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: {
            color: gridColor
          },
          grid: {
            color: gridColor
          },
          pointLabels: {
            color: labelColor,
            font: {
              size: 11,
              family: "'Plus Jakarta Sans', sans-serif",
              weight: '600'
            }
          },
          suggestedMin: 0,
          suggestedMax: 100,
          ticks: {
            stepSize: 25,
            display: false,
            backdropColor: 'transparent'
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: labelColor,
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              weight: '600',
              size: 12
            },
            padding: 15
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw}%`;
            }
          }
        }
      }
    }
  });
}
