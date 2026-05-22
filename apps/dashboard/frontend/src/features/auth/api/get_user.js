export async function checkAuthStatus() {
    return !!localStorage.getItem('token');
}