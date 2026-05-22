let tokenExists = false;

export function setTokenStatus(status) {
    tokenExists = status;
}

export async function checkAuthStatus() {
    return tokenExists;
}