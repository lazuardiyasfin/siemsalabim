import { describe, test, expect, afterEach, vi } from "vitest";
import { getHistoricalAlerts } from "../api/get-alerts.js";
import { apiClient } from "../../../lib/api-client.js";

describe("getHistoricalAlerts", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    test("should forward default query parameters to the apiClient", async () => {
        const mockResponseData = [{ id: 1, rule_id: "test_rule" }];        
        
        const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockResponseData);
        
        const data = await getHistoricalAlerts();

        expect(getSpy).toHaveBeenCalledWith("/api/alerts?range=1h");
        expect(data).toEqual(mockResponseData);
    });

    test("should append the severity filter to the relative endpoint string", async () => {
        const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce([]);
        
        await getHistoricalAlerts("24h", "HIGH");

        expect(getSpy).toHaveBeenCalledWith("/api/alerts?range=24h&severity=HIGH");
    });

    test("should bubble up errors thrown by the apiClient wrapper", async () => {
        const networkError = new Error("Unexpected error: 500");
        vi.spyOn(apiClient, "get").mockRejectedValueOnce(networkError);

        await expect(getHistoricalAlerts()).rejects.toThrow("Unexpected error: 500");
    });
});