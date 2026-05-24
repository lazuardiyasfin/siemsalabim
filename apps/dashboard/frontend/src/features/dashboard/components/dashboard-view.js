import '../assets/dashboard.css'
import { API_CONFIG } from "../../../config/env.js";
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

let socket = null;
let reconnectTimeout = null;
let isForceClosed = false;

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
    isForceClosed = false;
    if (reconnectTimeout) clearTimeout(reconnectTimeout);

    initStats();
    initEventsOverTimeChart();
    initLogTypesChart();
    initAlertsTable([]);
    initAttackerMap();

    document.getElementById('dashboard-refresh-btn')?.addEventListener('click', () => {
        initDashboard();
    });

    connectDashboardWebSocket();

    return () => {
        isForceClosed = true;
        if (reconnectTimeout) clearTimeout(reconnectTimeout);
        if (socket) {
            socket.close();
            socket = null;
        }
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

function connectDashboardWebSocket() {
    if (isForceClosed) return;

    const apiBaseUrl = API_CONFIG.BASE_URL || 'http://localhost:8001';
    const wsUrl = apiBaseUrl.replace(/^http/, 'ws') + '/ws/events';
    
    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        try {
            const envelope = JSON.parse(event.data);
            const isAlert = envelope.rule_id || envelope.type?.toUpperCase() === 'ALERT';

            if (isAlert) {
                const alertData = envelope.rule_id ? envelope : envelope.data;
                handleAlertMetrics(alertData);
                return;
            }

            handleSystemMetrics(envelope);
        } catch (err) {
            console.error('Error parsing stream packet:', err);
        }
    };

    socket.onclose = () => {
        if (isForceClosed) return;
        console.warn('Stream disconnected. Reconnecting in 5 seconds...');
        reconnectTimeout = setTimeout(connectDashboardWebSocket, 5000);
    };

    socket.onerror = (error) => {
        console.error('Stream network failure:', error);
        socket.close();
    };
}