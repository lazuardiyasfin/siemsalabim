export function renderAuthLayout(contentHtml) {
    return `
    <div class="auth-container">
        <div class="auth-card">
            ${contentHtml}
        </div>
    </div>
    `;
}