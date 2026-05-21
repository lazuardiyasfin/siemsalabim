import { initDashboard } from "../components/layout/dashboard-layout";
import { initDashboardCharts } from "../components/widgets/dashboard-widgets";
import mockData from "../services/mockSecurityData.json"

initDashboard();
initDashboardCharts(mockData);