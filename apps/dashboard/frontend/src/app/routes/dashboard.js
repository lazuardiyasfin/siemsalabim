import { renderAppLayout } from "../../components/layouts/app-layout"
import { renderDashboard, initDashboard } from "../../features/dashboard/components/dashboard-view"
import mockData from '../../testing/mocks/mockSecurityData.json'

export const dashboardRoutes = [
    {
        path: '/',
        render: () => renderAppLayout(renderDashboard()),
        init: () => initDashboard(mockData),
        requiresAuth: true
    }
]