import { initDashboard } from "../components/layout/dashboard-layout";
import { initDashboardWidgets } from "../components/widgets/dashboard-widgets";
import mockData from "../services/mockSecurityData.json"

initDashboard();
initDashboardWidgets(mockData);