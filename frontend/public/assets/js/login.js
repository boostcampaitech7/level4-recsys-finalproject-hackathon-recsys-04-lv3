// 로그인 폼 제출 이벤트
document.getElementById('loginForm').addEventListener('submit', async (event) => {
  event.preventDefault(); // 기본 제출 동작 방지

  // 입력된 아이디와 비밀번호 가져오기
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  // 간단한 로그인 검증 (데모용)
  try {
    const response = await fetch("http://localhost:8000/api/v1/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: username, password: password }),
    });

    const result = await response.json();
    if (response.ok) {
      // 로그인 성공 시
      alert('로그인 성공!');
      window.location.href = 'index.html'; // 새 페이지로 이동
      localStorage.setItem("user_id", result.user_id);
    } else {
      // 로그인 실패 시
      document.getElementById("status-message").innerText = '아이디나 비밀번호가 잘못됐습니다.';
    }
  } catch (error) {
    document.getElementById("status-message").innerText = "네트워크 오류가 발생했습니다.";
  }

});
