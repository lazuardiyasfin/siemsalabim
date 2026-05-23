import { API_CONFIG } from "../config/env";

async function request(endpoint, options = {}) {
    const url = `${API_CONFIG.API_BASE_URL}${endpoint}`;

    const fetchOptions = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        credentials: 'same-origin', 
    };

    try {
        const response = await fetch(url, fetchOptions);

        if (response.status === 401) {
            globalThis.location.href = '/login';
            throw new Error('Authentication required. Please log in.');
        }

        if (!response.ok) {
            throw new Error(`Unexpected error: ${response.status}`);
        }

        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('Request Error:', error);
        throw error;
    }
}

export const apiClient = {
    get: (endpoint, options) => request(endpoint, { ...options, method: 'GET' }),
    post: (endpoint, body, options) => request(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),
    put: (endpoint, body, options) => request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),
    delete: (endpoint, options) => request(endpoint, { ...options, method: 'DELETE' }),
};