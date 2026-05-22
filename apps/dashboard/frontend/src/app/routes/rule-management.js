import { renderAppLayout } from "../../components/layouts/app-layout";
import { renderRuleManagement } from "../../features/rule-management/components/rule-management-view";

export const ruleManagementRoutes = [
    {
        path: '/rules',
        render: () => renderAppLayout(renderRuleManagement()),
        requiresAuth: true
    }
];