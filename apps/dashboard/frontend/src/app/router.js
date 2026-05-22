import { dashboardRoutes } from "./routes/dashboard";

const routes = [
    ...dashboardRoutes
];

function handleRouting() {
    const path = globalThis.location.pathname;
    const route = routes.find(r => r.path === path);
    const appContainer = document.getElementById('app');

    if (!route) {
        appContainer.innerHTML = `<h1>404 - Not Found</h1>`;
        return;
    }

    appContainer.innerHTML = route.render();
    
    if (route.init) {
        route.init();
    }
}

export function initRouter() {
    globalThis.addEventListener('popstate', handleRouting);
    handleRouting();
}