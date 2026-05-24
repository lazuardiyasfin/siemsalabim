export function renderAlertsTable() {
    return `
    <section class="widget-card col-span-8">
        <h3 class="widget-title">Recent Alerts</h3>
        <div class="table-wrapper">
            <table class="alerts-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Rule Name</th>
                        <th>Severity</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody id="alerts-table-body">
                    <tr id="table-empty-row">
                        <td colspan="4" style="text-align: center; color: #6b7280;">
                            Waiting for live alerts...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </section>
    `;
}

export function initAlertsTable(initialAlerts = []) {
    const tbody = document.getElementById('alerts-table-body');
    if (!tbody) return;

    // Clear table body
    tbody.innerHTML = '';

    if (initialAlerts.length === 0) {
        tbody.innerHTML = `
        <tr id="table-empty-row">
            <td colspan="4" style="text-align: center; color: #6b7280;">
                Waiting for live alerts...
            </td>
        </tr>`;
        return;
    }

    initialAlerts.forEach(alert => appendAlertsRow(alert));
}

export function appendAlertsRow(alertData) {
    const tbody = document.getElementById('alerts-table-body');
    if (!tbody || !alertData) return;

    // Remove the "Waiting for live alerts" placeholder row if it exists
    document.getElementById('table-empty-row')?.remove();

    const row = document.createElement('tr');
    row.className = `severity-${alertData.severity?.toLowerCase() || 'medium'}`;

    const timestamp = alertData.timestamp 
        ? new Date(alertData.timestamp).toLocaleString() 
        : 'n/a';

    row.innerHTML = `
        <td>${timestamp}</td>
        <td><strong>${alertData.rule_name || 'Unknown Rule'}</strong></td>
        <td><span class="badge">${alertData.severity || 'UNKNOWN'}</span></td>
        <td>${alertData.description || ''}</td>
    `;

    // Prepend to show the newest alerts at the top of the table
    tbody.insertBefore(row, tbody.firstChild);

    // Optional: Keep the table performance stable by limiting to top 50 rows
    if (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }
}