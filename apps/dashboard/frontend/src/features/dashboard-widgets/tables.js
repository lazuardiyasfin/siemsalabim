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