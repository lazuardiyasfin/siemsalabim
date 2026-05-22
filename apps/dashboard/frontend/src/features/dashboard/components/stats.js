export function renderStats() {
    return `
    <section class="stat-card col-span-2">
        <h3 class="stat-title">Access events</h3>
        <div class="stat-value" id="count-access">n/a</div>
        <span class="stat-label">Count</span>
    </section>

    <section class="stat-card col-span-2">
        <h3 class="stat-title">Threat events</h3>
        <div class="stat-value" id="count-threat">n/a</div>
        <span class="stat-label">Count</span>
    </section>

    <section class="stat-card col-span-2">
        <h3 class="stat-title">Audit events</h3>
        <div class="stat-value" id="count-audit">n/a</div>
        <span class="stat-label">Count</span>
    </section>
    
    <section class="stat-card col-span-2">
        <h3 class="stat-title">Endpoint events</h3>
        <div class="stat-value" id="count-endpoint">n/a</div>
        <span class="stat-label">Count</span>
    </section> 
    `;
}

export function initStats(statsData) {
    document.getElementById('count-access').textContent = statsData.accessEvents;
    document.getElementById('count-threat').textContent = statsData.threatEvents;
    document.getElementById('count-audit').textContent = statsData.auditEvents;
    document.getElementById('count-endpoint').textContent = statsData.endpointEvents;
}