import { renderAppLayout } from "../../components/layouts/app-layout";
import { initRuleManagement, renderRuleManagement } from "../../features/rule-management/components/rule-management-view";
import mockData from '../../testing/mocks/mockRules.json'

export const ruleManagementRoutes = [
    {
        path: '/rules',
        title: 'Manage Rules - Siemsalabim',
        render: () => renderAppLayout(renderRuleManagement()),
        init: () => initRuleManagement(mockData),
        requiresAuth: true
    }
];