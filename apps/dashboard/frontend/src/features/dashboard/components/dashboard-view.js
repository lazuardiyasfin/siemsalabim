import '../assets/dashboard.css'
import { getHistoricalAlerts } from '../api/get-alerts.js';
import { connectDashboardWebSocket } from '../api/stream-events.js';
import { 
    renderStats, 
    initStats, 
    incrementTotalAlerts, 
    incrementCriticalAlerts, 
    updateActiveExporters, 
    updateEPS 
} from './stats.js';
import { renderEventsLineChart, initEventsOverTimeChart, addEventToTimeline } from './events-line-chart.js';
import { renderLogTypesChart, initLogTypesChart, updateLogTypeVolume } from './log-types-chart.js';
import { renderAlertsTable, initAlertsTable, appendAlertsRow } from './tables.js';
import { renderMap, initAttackerMap, addAttackerLocation } from './map.js';

export function renderDashboard() {
    return `
    <div class="dashboard-header">
        <div class="header-title"><h1>Security Overview</h1></div>
        <menu class="dashboard-toolbar">
            <div class="time-filter">
                <select class="select-time-preset">
                    <option value="1h">Last 1 hour</option>
                    <option value="24h" selected>Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                </select>
                <button>Show Dates</button>
            </div>
            
            <button id="dashboard-refresh-btn">Refresh</button>
        </menu>
    </div>
    <div class="dashboard-grid">
        <div class="main-column">
            <div class="stats-wrapper">
                ${renderStats()}
            </div>
            ${renderEventsLineChart()}
            ${renderAlertsTable()}
        </div>
        
        <div class="side-column">
            ${renderMap()}
            ${renderLogTypesChart()}
        </div>
    </div>
    `;
}

export function initDashboard() {
    initStats();
    initEventsOverTimeChart();
    initLogTypesChart();
    initAlertsTable([]);
    initAttackerMap();

    async function seedHistoricalData() {
        try {
            const historicalData = await getHistoricalAlerts();
            initAlertsTable(historicalData);

            historicalData.forEach(alert => {
                try { 
                    incrementTotalAlerts(); 
                } catch (e) { 
                    console.error('Failed to seed total alerts metric:', e); 
                }
                
                try {
                    const severity = alert.severity?.toUpperCase();
                    if (severity === 'CRITICAL' || severity === 'HIGH') incrementCriticalAlerts();
                } catch (e) { 
                    console.error('Failed to seed critical alerts metric:', e); 
                }
                
                try {
                    const program = alert.source_events?.[0]?.program;
                    if (program) updateLogTypeVolume(program);
                } catch (e) { 
                    console.error('Failed to seed log type volume chart:', e); 
                }
                
                try {
                    if (alert.timestamp) addEventToTimeline(alert.timestamp);
                } catch (e) { 
                    console.error('Failed to seed event timeline chart:', e); 
                }
                
                try {
                    const ip = alert.source_events?.[0]?.decoded?.src_ip;
                    if (alert.lat && alert.lon) addAttackerLocation(alert.lat, alert.lon, ip);
                } catch (e) { 
                    console.error('Failed to seed attacker map coordinates:', e); 
                }
            });
        } catch (err) {
            console.error("Failed to seed initial dashboard dataset:", err);
        }
    }

    seedHistoricalData();

    const refreshBtn = document.getElementById('dashboard-refresh-btn');
    if (refreshBtn) {
        refreshBtn.onclick = () => initDashboard();
    }

    const disconnectStream = connectDashboardWebSocket(handleAlertMetrics, handleSystemMetrics);

    return () => {
        disconnectStream();
    };
}

function handleAlertMetrics(alertData) {
    if (!alertData) return;

    try { 
        incrementTotalAlerts(); 
    } catch (err) { console.error('Failed to update Stats counter:', err); }
    
    try {
        const severity = alertData.severity?.toUpperCase();
        if (severity === 'CRITICAL' || severity === 'HIGH') {
            incrementCriticalAlerts();
        }
    } catch (err) { console.error('Failed to update Critical counter:', err); }
    
    try {
        const program = alertData.source_events?.[0]?.program;
        if (program) {
            updateLogTypeVolume(program);
        }
    } catch (err) { console.error('Failed to update Doughnut Chart:', err); }

    try {
        if (alertData.timestamp) {
            addEventToTimeline(alertData.timestamp);
        }
    } catch (err) { console.error('Failed to update Timeline Line Chart:', err); }

    try {
        appendAlertsRow(alertData);
    } catch (err) { console.error('Failed to append Table Row:', err); }

    try {
        const ip = alertData.source_events?.[0]?.decoded?.src_ip;
        if (alertData.lat && alertData.lon) {
            addAttackerLocation(alertData.lat, alertData.lon, ip);
        }
    } catch (err) { console.error('Failed to update Map marker:', err); }
}

function handleSystemMetrics(envelope) {
    const messageType = envelope.type?.toUpperCase();
    switch (messageType) {
        case 'EPS_UPDATE':
            updateEPS(envelope.data?.value || envelope.value);
            break;
        case 'EXPORTER_STATUS':
            updateActiveExporters(envelope.data?.count || envelope.count);
            break;
        default:
            console.debug('Unhandled message wrapper structure:', envelope);
    }
}