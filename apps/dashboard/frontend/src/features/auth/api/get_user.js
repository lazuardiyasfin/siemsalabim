export async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/me', {
            credentials: "same-origin"
        });
        return response.ok;
    } catch {
        return false;
    }
}   