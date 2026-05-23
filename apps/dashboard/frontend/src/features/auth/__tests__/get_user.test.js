import { describe, it, expect, vi, beforeEach } from 'vitest';
import { checkAuthStatus, clearAuthState } from '../api/get_user';

describe('Auth State Management', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        clearAuthState(); 
    });

    it('Should fetch user info on first call and use cache on subsequent calls', async () => {
        const mockUser = { username: 'admin' };
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockUser
        });
        vi.stubGlobal('fetch', fetchMock);

        // Should trigger network request
        const result1 = await checkAuthStatus();
        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(result1).toEqual(mockUser);

        // Should return cached data without calling fetch again
        const result2 = await checkAuthStatus();
        expect(fetchMock).toHaveBeenCalledTimes(1); 
        expect(result2).toEqual(mockUser);
    });

    it('Should trigger a new network request after clearAuthState is called', async () => {
        const mockUser = { username: 'admin' };
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockUser
        });
        vi.stubGlobal('fetch', fetchMock);

        await checkAuthStatus();
        expect(fetchMock).toHaveBeenCalledTimes(1);

        // Clear the memory state
        clearAuthState();

        // Should fetch again from the server
        await checkAuthStatus();
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it('Should return null and not cache the state if the API response is not ok', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));

        const result = await checkAuthStatus();
        expect(result).toBeNull();
    });
});