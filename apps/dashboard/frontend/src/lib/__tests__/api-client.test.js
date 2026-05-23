import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../api-client';
import { API_CONFIG } from '../../config/env';

describe('apiClient', () => {
    beforeEach(() => {
        vi.stubGlobal('fetch', vi.fn());
        vi.stubGlobal('location', { origin: 'http://localhost', href: '' });
        vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    it('Should send GET request with correct config', async () => {
        const mockResponse = { data: 'sukses' };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => mockResponse,
        });

        const data = await apiClient.get('/api/resource');

        expect(globalThis.fetch).toHaveBeenCalledWith(`${API_CONFIG.API_BASE_URL}/api/resource`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
        });
        expect(data).toEqual(mockResponse);
    });

    it('Should send POST request with the body', async () => {
        const bodyData = { name: 'test' };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            status: 201,
            json: async () => ({ id: 1 }),
        });

        await apiClient.post('/api/resource', bodyData);

        expect(globalThis.fetch).toHaveBeenCalledWith(`${API_CONFIG.API_BASE_URL}/api/resource`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData),
            credentials: 'same-origin',
        });
    });

    it('Should redirect to /login if status code 401 is received', async () => {
        globalThis.fetch.mockResolvedValue({
            ok: false,
            status: 401,
        });

        await expect(apiClient.get('/api/secure')).rejects.toThrow('Authentication required. Please log in.');
        expect(globalThis.location.href).toBe('/login');
    });

    it('Should send error message if the response is not ok', async () => {
        globalThis.fetch.mockResolvedValue({
            ok: false,
            status: 500,
            json: async () => ({ message: 'Internal Server Error' }),
        });

        await expect(apiClient.get('/api/error')).rejects.toThrow('Unexpected error: 500');
    });
});