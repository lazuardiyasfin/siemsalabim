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

            <tbody>
                <tr>
                    <td>prod-app-server</td>
                    <td>exporter-linux-01</td>
                    <td><code>/var/log/auth.log</code></td>
                    <td>syslog</td>
                    <td><span class="status-active">Active</span></td>
                    <td>
                    <span class="action-delete" title="Delete Log Path" role="button" tabindex="0">
                        <i data-lucide="trash-2"></i>
                    </span>
                    </td>
                </tr>

                <tr>
                    <td>prod-app-server</td>
                    <td>exporter-nginx-01</td>
                    <td><code>/var/log/nginx/access.log</code></td>
                    <td>json</td>
                    <td><span class="status-active">Active</span></td>
                    <td>
                    <span class="action-delete" title="Delete Log Path" role="button" tabindex="0">
                        <i data-lucide="trash-2"></i>
                    </span>
                    </td>
                </tr>

                <tr>
                    <td>db-primary-srv</td>
                    <td>exporter-mysql-02</td>
                    <td><code>/var/log/mysql/error.log</code></td>
                    <td>text</td>
                    <td><span class="status-idle">Idle</span></td>
                    <td>
                    <span class="action-delete" title="Delete Log Path" role="button" tabindex="0">
                        <i data-lucide="trash-2"></i>
                    </span>
                    </td>
                </tr>      
            </tbody>
        </table>
    </div>
    `;
}