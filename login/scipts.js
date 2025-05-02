function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (username && password) {
        alert('Login attempt with Username: ' + username);
        // Add your login logic here (e.g., API call)
    } else {
        alert('Please fill in both username and password.');
    }
}