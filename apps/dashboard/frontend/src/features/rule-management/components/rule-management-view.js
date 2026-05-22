import '../assets/rule-management.css'

export function renderRuleManagement() {
    return `
    <div class="rules-header">
        <div class="header-title"><h1>Manage Custom Rules</h1></div>
        <menu class="rules-toolbar">            
            <button class="btn-add-rule">Add Custom Rule</button>
        </menu>
    </div>

    <div class="table-responsive">
        <table class="rules-table">
            <thead>
                <tr>
                    <th>Rule Name</th>
                    <th>Severity</th>
                    <th>Log Source</th>
                    <th>Threshold</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="rules-tbody">
                <tr>
                    <td>Vulnerability Scanner Detected</td>
                    <td><span class="severity-badge severity-medium">Medium</span></td>
                    <td><code>nginx</code></td>
                    <td>10 events / 60s</td>
                    <td>
                        <label class="switch">
                            <input type="checkbox" checked data-id="nginx_scanner_404">
                            <span class="slider"></span>
                        </label>
                    </td>
                    <td>
                        <div class="action-buttons">
                            <span class="action-edit" title="Edit Rule" role="button" tabindex="0" data-id="nginx_scanner_404">
                                <i data-lucide="pencil"></i>
                            </span>
                            <span class="action-delete" title="Delete Rule" role="button" tabindex="0" data-id="nginx_scanner_404">
                                <i data-lucide="trash-2"></i>
                            </span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    `;
}