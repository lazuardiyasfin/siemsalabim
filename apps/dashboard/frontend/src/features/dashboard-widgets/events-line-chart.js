import { 
    Chart, 
    LineController, 
    LineElement, 
    PointElement, 
    CategoryScale, 
    LinearScale,
    Colors
} from 'chart.js';

Chart.register(
    LineController, 
    LineElement, 
    PointElement, 
    CategoryScale, 
    LinearScale,
    Colors
);

let eventsOverTimeChart = null;

export function initEventsOverTimeChart(eventsData) {
    const ctx = document.getElementById('events-over-time');
    if (!ctx) {
        return;
    }

    if (eventsOverTimeChart != null) {
        eventsOverTimeChart.destroy();
    }

    eventsOverTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: eventsData.map(row => {
                const timestamp = new Date(row.timestamp);
                return timestamp.toLocaleString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                });
            }),
            datasets: [{
                data: eventsData.map(row => row.count)
            }]
        },
        options: {
            animation: false,
            plugins: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
}