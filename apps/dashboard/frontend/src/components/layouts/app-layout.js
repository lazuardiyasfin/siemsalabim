export function renderAppLayout(contentHtml) {
    return `
    <div class="dashboard-container">
        <header>
            <div class="logo">
                <a href="/" data-route>
                    <span>Siemsalabim</span>
                </a>
            </div>
            <div class="user-profile">
                <span class="user-name">Administrator</span>
            </div>
        </header>   

        <nav>
            <ul>
                <li><a href="/" data-route><i data-lucide="gauge" class="nav-icon"></i></a></li>
                <li><a href="/logs" data-route><i data-lucide="file-cog" class="nav-icon"></i></a></li>
                <li><a href="/rules" data-route><i data-lucide="shield-alert" class="nav-icon"></i></a></li>
            </ul>
        </nav> 

        <main>${contentHtml}</main>
    </div>
    `;
}