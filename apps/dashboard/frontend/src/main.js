import 'leaflet/dist/leaflet.css';
import './style.css';
import mockSecurityData from './testing/mocks/mockSecurityData.json';
import { initDashboard } from './features/dashboard/components/dashboard-view.js';

initDashboard(mockSecurityData);