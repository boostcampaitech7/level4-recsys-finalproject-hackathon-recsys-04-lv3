// 회원가입 폼 제출 이벤트
document.getElementById('signupForm').addEventListener('submit', function (event) {
  event.preventDefault(); // 기본 제출 동작 방지

  // 팝업 메시지 띄우기
  alert('가입이 완료되었습니다!');

  // 로그인 페이지로 이동
  window.location.href = 'login.html';
});
