import '../assets/login.css'

export function renderLogin() {
    return `
    <div class="logo-container">
        <span class="logo-text">Siemsalabim</span>
    </div>
    
    <form id="login-form">
        <input type="text" placeholder="Username" id="username" required>
        <input type="password" placeholder="Password" id="password" required>
        
        <div class="form-footer">
            <label>
                <input type="checkbox" id="remember-me"> Keep me signed in
            </label>
            <button type="submit" class="login-btn">Login</button>
        </div>
    </form>
    `;
}

export function initLogin(onSuccessCallback) {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (username === 'admin' && password === 'admin') {
            localStorage.setItem('token', 'mock-jwt-token');
            onSuccessCallback(); 
        } else {
            alert('Invalid credentials');
        }
    });
}