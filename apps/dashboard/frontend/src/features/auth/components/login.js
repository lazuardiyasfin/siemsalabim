import '../assets/login.css'

export function renderLogin() {
    return `
    <div class="logo-container">
        <span class="logo-text">Siemsalabim</span>
    </div>
    
    <form>
        <input type="text" placeholder="Username" required>
        <input type="password" placeholder="Password" required>
        
        <div class="form-footer">
            <label>
                <input type="checkbox" id="remember-me"> Keep me signed in
            </label>
            <button type="submit" class="login-btn">Login</button>
        </div>
    </form>
    `;
}