export async function loginUser(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch('/login', {
        method: 'POST',
        body: formData,
        credentials: "same-origin" 
    });
    
    return response.ok;
}