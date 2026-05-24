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
const MAX_TIMELINE_POINTS = 15;

export function renderEventsLineChart() {
    return `
    <section class="widget-card col-span-8">
        <h3 class="widget-title">Events over time</h3>
        <div class="chart-wrapper">
            <canvas id="events-over-time"></canvas>
        </div>
    </section>
    `;
}

export function initEventsOverTimeChart() {
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
            labels: [],
            datasets: [{
                data: [],
                tension: 0.2
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
                },
                colors: {
                    forceOverride: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

export function addEventToTimeline(timestampString) {
    if (!eventsOverTimeChart) return;

    const timestamp = new Date(timestampString);
    const timeLabel = timestamp.toLocaleString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });

    const labels = eventsOverTimeChart.data.labels;
    const dataset = eventsOverTimeChart.data.datasets[0].data;
    const index = labels.indexOf(timeLabel);

    if (index !== -1) {
        dataset[index] += 1;
    } else {
        labels.push(timeLabel);
        dataset.push(1);

        if (labels.length > MAX_TIMELINE_POINTS) {
            labels.shift();
            dataset.shift();
        }
    }

    eventsOverTimeChart.update();
}