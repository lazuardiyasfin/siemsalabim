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

export function initLogTypesChart(logVolumesData) {
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
            labels: logVolumesData.map(row => row.type),
            datasets: [{
                data: logVolumesData.map(row => row.volume)
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
                }
            }
        }
    });
}
