import { API_CONFIG } from "../../../config/env.js";

let socket = null;
let reconnectTimeout = null;
let isForceClosed = false;

export function connectDashboardWebSocket(onAlert, onSystemMetric) {
    isForceClosed = false;
    if (reconnectTimeout) clearTimeout(reconnectTimeout);

    const apiBaseUrl = API_CONFIG.API_BASE_URL;
    const wsUrl = apiBaseUrl.replace(/^http/, 'ws') + '/ws/events';
    
    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        try {
            const envelope = JSON.parse(event.data);
            const isAlert = envelope.rule_id || envelope.type?.toUpperCase() === 'ALERT';

            if (isAlert) {
                const alertData = envelope.rule_id ? envelope : envelope.data;
                onAlert(alertData);
                return;
            }

            onSystemMetric(envelope);
        } catch (err) {
            console.error('Error parsing stream packet:', err);
        }
    };

    socket.onclose = () => {
        if (isForceClosed) return;
        console.warn('Stream disconnected. Reconnecting in 5 seconds...');
        reconnectTimeout = setTimeout(() => {
            connectDashboardWebSocket(onAlert, onSystemMetric);
        }, 5000);
    };

    socket.onerror = (error) => {
        console.error('Stream network failure:', error);
        socket.close();
    };

    return () => {
        isForceClosed = true;
        if (reconnectTimeout) clearTimeout(reconnectTimeout);
        if (socket) {
            socket.close();
            socket = null;
        }
    };
}