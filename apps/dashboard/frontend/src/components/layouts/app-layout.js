export function renderAppLayout(contentHtml) {
    return `
    <div class="dashboard-container">
        <header>
            <div class="logo">Siemsalabim</div>
            <div class="user-profile">
                <span class="user-name">Administrator</span>
            </div>
        </header>   

        <nav>
            <ul>
                <li><a href=""><i data-lucide="gauge" class="nav-icon"></i></a></li>
                <li><a href=""><i data-lucide="file-cog" class="nav-icon"></i></a></li>
                <li><a href=""><i data-lucide="shield-alert" class="nav-icon"></i></a></li>
            </ul>
        </nav> 

        <main>${contentHtml}</main>
    </div>
    `;
}