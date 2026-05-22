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