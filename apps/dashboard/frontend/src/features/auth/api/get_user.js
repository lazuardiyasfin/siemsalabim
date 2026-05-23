let currentUser = null;

export async function checkAuthStatus() {
    if (currentUser) return currentUser;

    try {
        const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (response.ok) {
            currentUser = await response.json();
            return currentUser;
        }
    } catch (error) {
        console.error('Gagal memeriksa otentikasi:', error);
    }

    currentUser = null;
    return null;
}   

export function clearAuthState() {
    currentUser = null;
}