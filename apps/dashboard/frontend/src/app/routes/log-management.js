import { renderAppLayout } from "../../components/layouts/app-layout";
import {  renderLogManagement } from "../../features/log-management/components/log-management-view";

export const logManagementRoutes = [
    {
        path: '/logs',
        render: () => renderAppLayout(renderLogManagement()),
        requiresAuth: true
    }
];