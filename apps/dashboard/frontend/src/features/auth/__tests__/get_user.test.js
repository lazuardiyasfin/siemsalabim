import { describe, it, expect, vi, beforeEach } from 'vitest';
import { checkAuthStatus } from '../api/get_user';

describe('checkAuthStatus()', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('Should return true if token exists in localStorage', async () => {
        const mockGetItem = vi.fn().mockReturnValue('jwt-token');
        
        vi.stubGlobal('localStorage', { getItem: mockGetItem });

        const result = await checkAuthStatus();

        expect(mockGetItem).toHaveBeenCalledWith('token');
        expect(result).toBe(true);
    });

    it('Should return false if token does not exist in localStorage', async () => {
        const mockGetItem = vi.fn().mockReturnValue(null);
        vi.stubGlobal('localStorage', { getItem: mockGetItem });

        const result = await checkAuthStatus();

        expect(result).toBe(false);
    });
});