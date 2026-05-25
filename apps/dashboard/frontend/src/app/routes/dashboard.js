import { renderAppLayout } from "../../components/layouts/app-layout";
import { renderDashboard, initDashboard } from "../../features/dashboard/components/dashboard-view";

let closeDashboardStream = null;

export const dashboardRoutes = [
    {
        path: '/',
        title: 'Security Overview - Siemsalabim',
        render: () => renderAppLayout(renderDashboard()),
        init: () => {
            // Clear any existing active stream connection
            if (closeDashboardStream) {
                closeDashboardStream();
            }

            // Initialize UI components and start the stream
            closeDashboardStream = initDashboard();
        },
        leave: () => {
            // Clean up and terminate the connection when navigating away
            if (closeDashboardStream) {
                closeDashboardStream();
                closeDashboardStream = null;
            }
        },
        requiresAuth: true
    }
];