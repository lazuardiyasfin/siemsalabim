import { renderAppLayout } from "../../components/layouts/app-layout";
import { initLogManagement, renderLogManagement } from "../../features/log-management/components/log-management-view";
import mockData from '../../testing/mocks/mockLogPath.json'

export const logManagementRoutes = [
    {
        path: '/logs',
        title: 'Manage Logs - Siemsalabim',
        render: () => renderAppLayout(renderLogManagement()),
        init: () => initLogManagement(mockData),
        requiresAuth: true
    }
];