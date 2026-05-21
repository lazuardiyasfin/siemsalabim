import Chart from 'chart.js/auto';

export function initDashboardWidgets(data) {
    if (!data) {
        console.error('Initialization failed: No data provided.');
        return;
    }

    initStats(data.stats);
    initEventsOverTimeChart(data.eventsOverTime);
    initLogTypesChart(data.logTypesVolume);
    initSummaryTable(data.summaryOfEvents);
}

let eventsOverTimeChart = null;
let logTypesChart = null;

function initEventsOverTimeChart(eventsData) {
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

function initLogTypesChart(logVolumesData) {
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

function initStats(statsData) {
    document.getElementById('count-access').textContent = statsData.accessEvents;
    document.getElementById('count-threat').textContent = statsData.threatEvents;
    document.getElementById('count-audit').textContent = statsData.auditEvents;
    document.getElementById('count-endpoint').textContent = statsData.endpointEvents;
}

function initSummaryTable(alertsData) {
    const summaryTBody = document.getElementById('summary-tbody');
    if (!summaryTBody) {
        return;
    }
    
    summaryTBody.innerHTML = alertsData.map(row => `
        <tr>
            <td>${row.rule}</td>
            <td>${row.severity}</td>
            <td>${row.events}</td>
        </tr>    
    `).join('');
}