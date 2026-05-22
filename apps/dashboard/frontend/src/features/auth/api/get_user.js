let tokenExists = false;

export function setTokenStatus(status) {
    tokenExists = status;
}

export async function checkAuthStatus() {
    const token = tokenExists;
    if (token) {
        return true;
    } else {
        return false;
    }
}