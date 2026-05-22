import { createIcons, Gauge, FileCog, ShieldAlert } from 'lucide';
import { renderStats, initStats } from './stats.js';
import { renderEventsLineChart, initEventsOverTimeChart } from './events-line-chart.js';
import { renderLogTypesChart, initLogTypesChart } from './log-types-chart.js';
import { renderTables, initSummaryTable } from './tables.js';
import { renderMap, initAttackerMap } from './map.js';

export function renderDashboard() {
    return `
    <div class="dashboard-header">
        <div class="header-title"><h1>Security Overview</h1></div>
        <menu class="dashboard-toolbar">
            <div class="time-filter">
                <select class="select-time-preset">
                    <option value="24h" selected>Last 24 hours</option>
                </select>
            </div>
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
}

export function initDashboard(mockData) {
    createIcons({
        icons: { Gauge, FileCog, ShieldAlert }
    });

    if (mockData) {
        initStats(mockData.stats);
        initEventsOverTimeChart(mockData.eventsOverTime);
        initLogTypesChart(mockData.logTypesVolume);
        initSummaryTable(mockData.summaryOfEvents);
        initAttackerMap(mockData.attackerOrigin);
    }
}