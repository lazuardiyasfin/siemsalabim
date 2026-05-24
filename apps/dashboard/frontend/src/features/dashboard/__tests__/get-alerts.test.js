import { describe, test, expect, afterEach, vi } from "vitest";
import { getHistoricalAlerts } from "../api/get-alerts.js";
import { apiClient } from "../../../lib/api-client.js";

vi.mock("../../../lib/apiClient.js", () => ({
    apiClient: {
        get: vi.fn()
    }
}));

describe("getHistoricalAlerts", () => {
    afterEach(() => {
        // Automatically restores all spy methods back to their original implementation between runs
        vi.restoreAllMocks();
    });

    test("should forward default query parameters to the apiClient", async () => {
        const mockResponseData = [{ id: 1, rule_id: "test_rule" }];
        
        // Spy directly on the imported apiClient object's 'get' method
        const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce(mockResponseData);

        const data = await getHistoricalAlerts();

        expect(getSpy).toHaveBeenCalledWith("/api/alerts?limit=100");
        expect(data).toEqual(mockResponseData);
    });

    test("should append the severity filter to the relative endpoint string", async () => {
        const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce([]);

        await getHistoricalAlerts(50, "HIGH");

        expect(getSpy).toHaveBeenCalledWith("/api/alerts?limit=50&severity=HIGH");
    });

    test("should bubble up errors thrown by the apiClient wrapper", async () => {
        const networkError = new Error("Unexpected error: 500");
        vi.spyOn(apiClient, "get").mockRejectedValueOnce(networkError);

        await expect(getHistoricalAlerts()).rejects.toThrow("Unexpected error: 500");
    });
});