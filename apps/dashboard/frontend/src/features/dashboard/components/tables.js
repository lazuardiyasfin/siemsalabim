export function renderTables() {
    return `
    <section class="widget-card col-span-8 row-span-2">
        <h3 class="widget-title">Summary of events</h3>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Severity</th>
                        <th>Events</th>
                    </tr>
                </thead>
                <tbody id="summary-tbody"></tbody>
            </table>
        </div>
    </section>
    `;
}

export function initSummaryTable(alertsData) {
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