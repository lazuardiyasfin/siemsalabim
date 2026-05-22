import { renderAppLayout } from "../../components/layouts/app-layout";
import { initLogManagement, renderLogManagement } from "../../features/log-management/components/log-management-view";
import mockData from '../../testing/mocks/mockLogPath.json'

export const logManagementRoutes = [
    {
        path: '/logs',
        render: () => renderAppLayout(renderLogManagement()),
        init: () => initLogManagement(mockData),
        requiresAuth: true
    }
];