// // signup.js
// document.getElementById('signupForm').addEventListener('submit', async (event) => {
//   event.preventDefault(); // 기본 제출 동작 방지

//   const username = document.getElementById('username').value;
//   const password = document.getElementById('password').value;

//   try {
//       const response = await fetch("http://localhost:8000/api/v1/auth/register", {
//           method: "POST",
//           headers: {
//               "Content-Type": "application/json",
//           },
//           body: JSON.stringify({ email: username, password: password }),
//       });

//       const result = await response.json();
//       if (response.ok) {
//           // 로그인 성공 시
//           alert('회원가입 성공!');
//           window.location.href = 'login.html'; // 새 페이지로 이동

//       } else {
//           // 로그인 실패 시
//           document.getElementById("status-message").innerText = '이미 존재하는 아이디입니다.';
//       }
//   } catch (error) {
//       document.getElementById("status-message").innerText = "네트워크 오류가 발생했습니다.";
//   }
// });
