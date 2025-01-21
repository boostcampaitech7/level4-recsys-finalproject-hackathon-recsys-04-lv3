// 로그인 폼 제출 이벤트
document.getElementById('loginForm').addEventListener('submit', function (event) {
  event.preventDefault(); // 기본 제출 동작 방지

  // 입력된 아이디와 비밀번호 가져오기
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  // 간단한 로그인 검증 (데모용)
  const correctUsername = "testuser"; // 올바른 아이디
  const correctPassword = "1234"; // 올바른 비밀번호

  if (username === correctUsername && password === correctPassword) {
    // 로그인 성공 시
    alert('로그인 성공!');
    window.location.href = 'index.html'; // 새 페이지로 이동
  } else {
    // 로그인 실패 시
    alert('아이디나 비밀번호가 잘못됐습니다.');
  }
});
