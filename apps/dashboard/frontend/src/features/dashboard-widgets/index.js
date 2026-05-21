import { initStats } from "./stats";
import { initEventsOverTimeChart } from "./events-line-chart";
import { initLogTypesChart } from "./log-types-chart";
import { initSummaryTable } from "./tables";
import { initAttackerMap } from "./map";
import mockData from './mockSecurityData.json';

export function initDashboardWidgets() {
    initStats(mockData.stats);
    initEventsOverTimeChart(mockData.eventsOverTime);
    initLogTypesChart(mockData.logTypesVolume);
    initSummaryTable(mockData.summaryOfEvents);
    initAttackerMap(mockData.attackerOrigin);
}
