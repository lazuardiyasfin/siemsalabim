import '../assets/log-management.css'

export function renderLogManagement() {
    return `
    <div class="logs-header">
        <div class="header-title"><h1>Manage Logs</h1></div>
        <menu class="logs-toolbar">            
            <button>Add Log Path</button>
        </menu>
    </div>

    <div class="table-responsive">
        <table class="logs-table">
            <thead>
                <tr>
                <th>Host</th>
                <th>Exporter ID</th>
                <th>Log Path</th>
                <th>Log Format</th>
                <th>Status</th>
                <th>Actions</th>
                </tr>
            </thead>
            <tbody id="logs-tbody">
            </tbody>
        </table>
    </div>
    `;
}

export function initLogManagement(logs) {
    const logsTbody = document.getElementById('logs-tbody');
    if (!logsTbody) return;

    logsTbody.innerHTML = logs.map(log => `
        <tr>
            <td>${log.host}</td>
            <td>${log.exporterId}</td>
            <td><code>${log.logPath}</code></td>
            <td>${log.logFormat}</td>
            <td><span class="${log.statusClass}">${log.status}</span></td>
            <td>
                <span class="action-delete" title="Delete Log Path" role="button" tabindex="0" data-id="${log.exporterId}">
                    <i data-lucide="trash-2"></i>
                </span>
            </td>
        </tr>
    `).join('');
}