import { createIcons, Gauge, FileCog, ShieldAlert } from 'lucide';
import { renderAppLayout } from '../../../components/layouts/app-layout.js';
import { renderStats, initStats } from './stats.js';
import { renderEventsLineChart, initEventsOverTimeChart } from './events-line-chart.js';
import { renderLogTypesChart, initLogTypesChart } from './log-types-chart.js';
import { renderTables, initSummaryTable } from './tables.js';
import { renderMap, initAttackerMap } from './map.js';

export function initDashboard(mockData) {
    const dashboardHtml = `
    <div class="dashboard-header">
        <div class="header-title">
            <h1>Security Overview</h1>
        </div>

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
            
            <button>Refresh</button>
        </menu>
    </div>

    <div class="dashboard-grid">
        ${renderStats()}
        ${renderMap()}
        ${renderEventsLineChart()}
        ${renderTables()}
        ${renderLogTypesChart()}
    </div>
    `;

    document.querySelector('#app').innerHTML = renderAppLayout(dashboardHtml);

    createIcons({
        icons: {
            Gauge,
            FileCog,
            ShieldAlert
        }
    });

    if (mockData) {
        initStats(mockData.stats);
        initEventsOverTimeChart(mockData.eventsOverTime);
        initLogTypesChart(mockData.logTypesVolume);
        initSummaryTable(mockData.summaryOfEvents);
        initAttackerMap(mockData.attackerOrigin);
    }
}