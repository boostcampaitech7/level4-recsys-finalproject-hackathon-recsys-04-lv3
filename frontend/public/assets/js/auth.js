// assets/js/auth.js
document.addEventListener('DOMContentLoaded', function () {
    const API_URL = 'http://localhost:8000/api/v1/auth';
    const statusMessage = document.getElementById('status-message');

    // 회원가입 폼 처리
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
                    // 회원가입 성공
                    showStatusMessage('회원가입이 완료되었습니다!', 'success');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1500);
                } else {
                    // 회원가입 실패
                    if (response.status === 400) {
                        showStatusMessage('이미 등록된 이메일입니다. 다른 이메일을 사용해주세요.', 'error');
                    } else {
                        showStatusMessage(data.message || '회원가입 중 오류가 발생했습니다.', 'error');
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                showStatusMessage('서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.', 'error');
            }
        });
    }

    // 로그인 폼 처리
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
                    // 로그인 성공
                    localStorage.clear();
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('userEmail', email);
                    window.location.href = 'main.html';
                } else {
                    // 로그인 실패
                    showStatusMessage(data.message || '이메일 또는 비밀번호가 올바르지 않습니다.', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showStatusMessage('서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.', 'error');
            }
        });
    }
});

// 상태 메시지 표시 함수
function showStatusMessage(message, type = 'error') {
    const statusMessage = document.getElementById('status-message');
    if (statusMessage) {
        statusMessage.textContent = message;
        statusMessage.className = 'status-message visible ' + type;
    }
}

// 로그아웃 함수
function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('userEmail');
    window.location.href = 'index.html';
}
