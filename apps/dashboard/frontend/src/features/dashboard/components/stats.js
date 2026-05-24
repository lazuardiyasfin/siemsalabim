let totalAlerts = 0;
let criticalAlerts = 0;

export function renderStats() {
    return `
    <section class="stat-card col-span-2">
        <h3 class="stat-title">Total Alerts</h3>
        <div class="stat-value" id="count-total">0</div>
        <span class="stat-label">Count</span>
    </section>

    <section class="stat-card col-span-2">
        <h3 class="stat-title">Critical Alerts</h3>
        <div class="stat-value" id="count-critical">0</div>
        <span class="stat-label">Count</span>
    </section>

    <section class="stat-card col-span-2">
        <h3 class="stat-title">Active Exporters</h3>
        <div class="stat-value" id="count-exporters">0</div>
        <span class="stat-label">Active</span>
    </section>
    
    <section class="stat-card col-span-2">
        <h3 class="stat-title">EPS</h3>
        <div class="stat-value" id="eps">0</div>
        <span class="stat-label">Event/sec</span>
    </section> 
    `;
}

export function initStats() {
    totalAlerts = 0;
    criticalAlerts = 0;
    
    const totalStat = document.getElementById('count-total');
    const criticalStat = document.getElementById('count-critical');
    const exportersStat = document.getElementById('count-exporters');
    const epsStat = document.getElementById('eps');

    if (totalStat) totalStat.textContent = totalAlerts;
    if (criticalStat) criticalStat.textContent = criticalAlerts;
    if (exportersStat) exportersStat.textContent = '0';
    if (epsStat) epsStat.textContent = '0';
}

export function incrementTotalAlerts() {
    totalAlerts++;
    const totalStat = document.getElementById('count-total');
    if (totalStat) totalStat.textContent = totalAlerts;
}

export function incrementCriticalAlerts() {
    criticalAlerts++;
    const criticalStat = document.getElementById('count-critical');
    if (criticalStat) criticalStat.textContent = criticalAlerts;
}

export function updateActiveExporters(count) {
    const exportersStat = document.getElementById('count-exporters');
    if (exportersStat) exportersStat.textContent = count;
}

export function updateEPS(value) {
    const epsStat = document.getElementById('eps');
    if (epsStat) epsStat.textContent = value;
}