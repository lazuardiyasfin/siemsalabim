import { describe, it, expect, vi, beforeEach } from 'vitest';
import { loginUser } from '../api/login';

describe('loginUser', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('Should return true and send correct FormData when login is successful', async () => {
        const fetchMock = vi.fn().mockResolvedValue({ ok: true });
        vi.stubGlobal('fetch', fetchMock);

        const result = await loginUser('admin', 'secret123');

        expect(fetchMock).toHaveBeenCalledWith('/login', expect.objectContaining({
            method: 'POST',
            credentials: 'same-origin'
        }));

        const formDataSent = fetchMock.mock.calls[0][1].body;
        expect(formDataSent.get('username')).toBe('admin');
        expect(formDataSent.get('password')).toBe('secret123');
        
        expect(result).toBe(true);
    });

    it('should return false when the server responds with an error', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));

        const result = await loginUser('wrong-user', 'wrong-pass');

        expect(result).toBe(false);
    });

    it('should throw an error if the network request fails', async () => {
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network Error')));

        await expect(loginUser('admin', 'secret123')).rejects.toThrow('Network Error');
    });
});