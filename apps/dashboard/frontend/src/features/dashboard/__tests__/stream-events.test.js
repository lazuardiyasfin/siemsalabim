import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { connectDashboardWebSocket } from "../api/stream-events";

vi.mock("../../../config/env.js", () => ({
    API_CONFIG: {
        API_BASE_URL: "http://localhost:8001"
    }
}));

describe("connectDashboardWebSocket", () => {
    let mockWebSocketInstance;
    let onAlertMock;
    let onSystemMetricMock;

    beforeEach(() => {
        vi.useFakeTimers();
        onAlertMock = vi.fn();
        onSystemMetricMock = vi.fn();

        globalThis.WebSocket = vi.fn().mockImplementation(function (url) {
            this.url = url;
            this.close = vi.fn();
            mockWebSocketInstance = this;
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.clearAllTimers();
        vi.useRealTimers();
    });

    test("should establish connection with corrected WebSocket protocol mapping", () => {
        const disconnect = connectDashboardWebSocket(onAlertMock, onSystemMetricMock);

        expect(globalThis.WebSocket).toHaveBeenCalledWith("ws://localhost:8001/ws/events");
        expect(typeof disconnect).toBe("function");
        disconnect();
    });

    test("should route incoming alert data packet to onAlert callback", () => {
        const disconnect = connectDashboardWebSocket(onAlertMock, onSystemMetricMock);
        
        const mockAlertPayload = { rule_id: "ssh_brute_force", severity: "HIGH" };
        const eventMessage = { data: JSON.stringify(mockAlertPayload) };
        
        mockWebSocketInstance.onmessage(eventMessage);

        expect(onAlertMock).toHaveBeenCalledWith(mockAlertPayload);
        expect(onSystemMetricMock).not.toHaveBeenCalled();
        disconnect();
    });

    test("should route incoming system telemetry data packet to onSystemMetric callback", () => {
        const disconnect = connectDashboardWebSocket(onAlertMock, onSystemMetricMock);
        
        const mockMetricPayload = { type: "EPS_UPDATE", value: 42 };
        const eventMessage = { data: JSON.stringify(mockMetricPayload) };
        
        mockWebSocketInstance.onmessage(eventMessage);

        expect(onSystemMetricMock).toHaveBeenCalledWith(mockMetricPayload);
        expect(onAlertMock).not.toHaveBeenCalled();
        disconnect();
    });

    test("should trigger automatic reconnection loop after 5 seconds on unexpected closure", () => {
        connectDashboardWebSocket(onAlertMock, onSystemMetricMock);
        
        expect(globalThis.WebSocket).toHaveBeenCalledTimes(1);

        mockWebSocketInstance.onclose();

        vi.advanceTimersByTime(5000);

        expect(globalThis.WebSocket).toHaveBeenCalledTimes(2);
    });

    test("should prevent reconnection loops when clean teardown handle is executed", () => {
        const disconnect = connectDashboardWebSocket(onAlertMock, onSystemMetricMock);
        
        expect(globalThis.WebSocket).toHaveBeenCalledTimes(1);

        disconnect();

        expect(mockWebSocketInstance.close).toHaveBeenCalledTimes(1);

        mockWebSocketInstance.onclose();
        vi.advanceTimersByTime(5000);

        expect(globalThis.WebSocket).toHaveBeenCalledTimes(1);
    });
});