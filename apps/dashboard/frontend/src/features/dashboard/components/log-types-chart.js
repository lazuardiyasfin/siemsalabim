import { 
    Chart, 
    DoughnutController, 
    ArcElement, 
    Legend,
    Colors
} from 'chart.js';

Chart.register(
    DoughnutController, 
    ArcElement, 
    Legend,
    Colors
);

let logTypesChart = null;

export function renderLogTypesChart() {
    return `
    <section class="widget-card col-span-6 row-span-2">
        <h3 class="widget-title">Log types volume breakdown</h3>
        <div class="chart-wrapper">
            <canvas id="log-types-breakdown"></canvas>
        </div>
    </section> 
    `;
}

export function initLogTypesChart() {
    const ctx = document.getElementById('log-types-breakdown');
    if (!ctx) {
        return;
    }

    if (logTypesChart != null) {
        logTypesChart.destroy();
    }

    logTypesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: []
            }]
        },
        options: {
            animation: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right'
                },
                tooltip: {
                    enabled: false
                },
                colors: {
                    forceOverride: true
                }
            }
        }
    });
}

export function updateLogTypeVolume(logType) {
    if (!logTypesChart) return;

    const labels = logTypesChart.data.labels;
    const dataset = logTypesChart.data.datasets[0].data;
    const index = labels.indexOf(logType);

    if (index !== -1) {
        dataset[index] += 1;
    } else {
        labels.push(logType);
        dataset.push(1);
    }

    logTypesChart.update();
}