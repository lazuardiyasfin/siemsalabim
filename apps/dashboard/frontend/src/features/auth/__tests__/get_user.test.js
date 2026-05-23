import { describe, it, expect, vi, beforeEach } from 'vitest';
import { checkAuthStatus } from '../api/get_user'; 

describe('checkAuthStatus', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('Should return true when the API response is successful', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
            ok: true
        }));

        const result = await checkAuthStatus();

        expect(globalThis.fetch).toHaveBeenCalledWith('/api/auth/me', {
            credentials: 'same-origin',
        });
        expect(result).toBe(true);
    });

    it('Should return false when the API response is not ok', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
            ok: false
        }));

        const result = await checkAuthStatus();

        expect(globalThis.fetch).toHaveBeenCalledWith('/api/auth/me', {
            credentials: 'same-origin',
        });
        expect(result).toBe(false);
    });

    it('should return false when a network error or exception occurs', async () => {
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network failure')));

        const result = await checkAuthStatus();

        expect(result).toBe(false);
    });
});