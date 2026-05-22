import { dashboardRoutes } from "./routes/dashboard";
import { checkAuthStatus } from "../features/auth/api/get_user";
import { authRoutes } from "./routes/auth";
import { logManagementRoutes } from "./routes/log-management";
import { createIcons, Gauge, FileCog, ShieldAlert, Trash2 } from 'lucide';

const routes = [
    ...dashboardRoutes,
    ...authRoutes,
    ...logManagementRoutes
];

async function handleRouting() {
    const path = globalThis.location.pathname;
    const route = routes.find(r => r.path === path);
    const appContainer = document.getElementById('app');

    if (!route) {
        appContainer.innerHTML = `<h1>404 - Not Found</h1>`;
        return;
    }

    const isAuthenticated = await checkAuthStatus();

    if (route.requiresAuth && !isAuthenticated) {
        navigateTo('/login');
        return;
    }

    appContainer.innerHTML = route.render();

    // Create icons only when on authenticated views
    if (route.requiresAuth) {
        createIcons({
            icons: { Gauge, FileCog, ShieldAlert, Trash2 }
        });
    }

    if (route.init) {
        route.init();
    }
}

export function navigateTo(path) {
    globalThis.history.pushState(null, null, path);
    handleRouting();
}

export function initRouter() {
    globalThis.addEventListener('popstate', handleRouting);

    globalThis.document.addEventListener('click', (e) => {
        const targetLink = e.target.closest('[data-route]');

        if (targetLink) {
            e.preventDefault();
            const path = targetLink.getAttribute('href');
            navigateTo(path);
        }
    });

    handleRouting();
}