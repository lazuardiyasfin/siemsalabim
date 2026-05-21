export function initStats(statsData) {
    document.getElementById('count-access').textContent = statsData.accessEvents;
    document.getElementById('count-threat').textContent = statsData.threatEvents;
    document.getElementById('count-audit').textContent = statsData.auditEvents;
    document.getElementById('count-endpoint').textContent = statsData.endpointEvents;
}