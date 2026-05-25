import { apiClient } from "../../../lib/api-client.js";

export async function getHistoricalAlerts(range = "1h", severity = "") {
    let endpoint = `/api/alerts?range=${range}`;
    
    if (severity) {
        endpoint += `&severity=${encodeURIComponent(severity)}`;
    }

    return await apiClient.get(endpoint);
}

export async function getDashboardStats() {
    return await apiClient.get('/stats');
}