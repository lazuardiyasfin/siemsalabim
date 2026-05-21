import { createIcons, Gauge, FileCog, ShieldAlert } from 'lucide';

export function initDashboard() {
    document.querySelector('#app').innerHTML = `
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

        <main>
            <div class="dashboard-header">
                <div class="header-title">
                    <h1>Security Overview</h1>
                </div>

                <menu class="dashboard-toolbar">
                    <div class="time-filter">
                        <select class="select-time-preset">
                            <option value="1h">Last 1 hour</option>
                            <option value="24h" selected>Last 24 hours</option>
                            <option value="7d">Last 7 days</option>
                            <option value="30d">Last 30 days</option>
                        </select>
                        <button>Show Dates</button>
                    </div>
                    
                    <button>Refresh</button>
                </menu>
            </div>

            <div class="dashboard-grid">
                <section class="stat-card col-span-2">
                    <h3 class="stat-title">Access events</h3>
                    <div class="stat-value" id="count-access">n/a</div>
                    <span class="stat-label">Count</span>
                </section>

                <section class="stat-card col-span-2">
                    <h3 class="stat-title">Threat events</h3>
                    <div class="stat-value" id="count-threat">n/a</div>
                    <span class="stat-label">Count</span>
                </section>

                <section class="stat-card col-span-2">
                    <h3 class="stat-title">Audit events</h3>
                    <div class="stat-value" id="count-audit">n/a</div>
                    <span class="stat-label">Count</span>
                </section>
                
                <section class="stat-card col-span-2">
                    <h3 class="stat-title">Endpoint events</h3>
                    <div class="stat-value" id="count-endpoint">n/a</div>
                    <span class="stat-label">Count</span>
                </section> 
                
                <section class="widget-card col-span-6 row-span-2">
                    <h3 class="widget-title">Attacker origin</h3>
                    <div class="map-wrapper">
                        <div id="map-container"></div>
                    </div>
                </section>                

                <section class="widget-card col-span-8">
                    <h3 class="widget-title">Events over time</h3>
                    <div class="chart-wrapper">
                        <canvas id="events-over-time"></canvas>
                    </div>
                </section>

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
                
                <section class="widget-card col-span-6 row-span-2">
                    <h3 class="widget-title">Log types volume breakdown</h3>
                    <div class="chart-wrapper">
                        <canvas id="log-types-breakdown"></canvas>
                    </div>
                </section>                
            </div>
        </main>
    </div>
    `;

    createIcons({
        icons: {
            Gauge,
            FileCog,
            ShieldAlert
        }
    });
}

