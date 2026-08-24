(() => {
  const dataElement = document.getElementById('production-chart-data');
  if (!dataElement || typeof Chart === 'undefined') return;

  const report = JSON.parse(dataElement.textContent);
  const colors = ['#f6c344', '#5dade2', '#58d68d', '#ec7063', '#af7ac5'];
  const commonOptions = (unit, currency = false) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { labels: { color: '#fff' } },
      tooltip: {
        callbacks: {
          label(context) {
            const value = Number(context.parsed.y);
            const formatted = currency
              ? `$${value.toFixed(2)}`
              : `${value.toFixed(1)} ${unit}`;
            return `${context.dataset.label}: ${formatted}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#ddd', maxRotation: 45, minRotation: 0 },
        grid: { color: 'rgba(255, 255, 255, 0.08)' },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: '#ddd',
          callback: currency ? (value) => `$${value}` : undefined,
        },
        grid: { color: 'rgba(255, 255, 255, 0.12)' },
      },
    },
  });

  const dataset = (label, values, color, width = 2) => ({
    label,
    data: values,
    borderColor: color,
    backgroundColor: color,
    borderWidth: width,
    pointRadius: values.length > 31 ? 1 : 3,
    tension: 0.25,
    fill: false,
  });

  const aircraftDatasets = Object.entries(report.aircraft_hours).map(
    ([registration, values], index) =>
      dataset(registration, values, colors[(index + 1) % colors.length]),
  );

  new Chart(document.getElementById('flight-hours-chart'), {
    type: 'line',
    data: {
      labels: report.labels,
      datasets: [
        dataset('Total flota', report.flight_hours, colors[0], 3),
        ...aircraftDatasets,
      ],
    },
    options: commonOptions('h'),
  });

  new Chart(document.getElementById('flight-income-chart'), {
    type: 'line',
    data: {
      labels: report.labels,
      datasets: [dataset('Ingreso', report.income_usd, colors[1], 3)],
    },
    options: commonOptions('USD', true),
  });

  new Chart(document.getElementById('flight-operating-income-chart'), {
    type: 'line',
    data: {
      labels: report.labels,
      datasets: [
        dataset('Ingreso operativo', report.operating_income_usd, colors[2], 3),
      ],
    },
    options: commonOptions('USD', true),
  });
})();
