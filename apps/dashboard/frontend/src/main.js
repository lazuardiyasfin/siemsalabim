import 'leaflet/dist/leaflet.css';
import './style.css';
import { initDashboard } from './layouts/dashboard'
import { initDashboardWidgets } from './features/dashboard-widgets';

initDashboard();
initDashboardWidgets();