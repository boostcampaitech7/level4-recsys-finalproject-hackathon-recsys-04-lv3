// assets/js/auth.js
document.addEventListener('DOMContentLoaded', function () {
    const API_URL = 'http://localhost:8000/api/v1/auth';
    const statusMessage = document.getElementById('status-message');

    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    alert('회원가입 성공!');
                    window.location.href = 'index.html';
                } else {
                    statusMessage.textContent = data.message || '이미 존재하는 이메일입니다. 다른 이메일을 사용해주세요.';
                }
            } catch (error) {
                statusMessage.textContent = '서버 오류가 발생했습니다.';
                console.error('Error:', error);
            }
        });
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    localStorage.clear();
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('userEmail', email);
                    window.location.href = 'main.html';
                } else {
                    statusMessage.textContent = data.message || '로그인 실패';
                }
            } catch (error) {
                statusMessage.textContent = '서버 오류가 발생했습니다.';
                console.error('Error:', error);
            }
        });
    }
});

function logout() {
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    window.location.href = 'index.html';
}
