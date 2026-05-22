import '../assets/rule-management.css'

export function renderRuleManagement() {
    return `
    <div class="rules-header">
        <div class="header-title"><h1>Manage Rules</h1></div>
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
            </tbody>
        </table>
    </div>
    `;
}

export function initRuleManagement(rules) {
    const rulesTbody = document.getElementById('rules-tbody');
    if (!rulesTbody) return;

    if (!rules || rules.length === 0) {
        rulesTbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No rules found</td></tr>';
        return;
    }

    rulesTbody.innerHTML = rules.map(rule => {
        const severity = rule.severity || 'medium';
        const severityLabel = severity.charAt(0).toUpperCase() + severity.slice(1);
        const count = rule.frequency?.count || 0;
        const window = rule.frequency?.window_seconds || 0;
        const isChecked = rule.status === 'active' || rule.status === true ? 'checked' : '';

        return `
            <tr>
                <td>${rule.name || 'Untitled Rule'}</td>
                <td><span class="severity-badge severity-${severity.toLowerCase()}">${severityLabel}</span></td>
                <td><code>${rule.program || '-'}</code></td>
                <td>${count} events / ${window}s</td>
                <td>
                    <label class="switch">
                        <input type="checkbox" ${isChecked} data-id="${rule.id}">
                        <span class="slider"></span>
                    </label>
                </td>
                <td>
                    <div class="action-buttons">
                        <span class="action-edit" title="Edit Rule" role="button" tabindex="0" data-id="${rule.id}">
                            <i data-lucide="pencil"></i>
                        </span>
                        <span class="action-delete" title="Delete Rule" role="button" tabindex="0" data-id="${rule.id}">
                            <i data-lucide="trash-2"></i>
                        </span>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}