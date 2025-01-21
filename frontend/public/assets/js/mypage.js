// localStorage에서 user_id를 가져옴
const userId = localStorage.getItem("user_id");

// user_id가 없으면 로그인 페이지로 리다이렉트
if (!userId) {
    window.location.href = "login.html";
} else {
    // FastAPI 서버로부터 유저 데이터를 가져옴
    fetch(`http://127.0.0.1:8000/api/v1/auth/user/${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("유저 정보를 가져오는 데 실패했습니다.");
            }
            return response.json();
        })
        .then(data => {
            // 데이터를 페이지에 렌더링
            document.querySelector(".profile-section .profile-item:nth-child(1) span").textContent = data.user_id;
            document.querySelector(".profile-section .profile-item:nth-child(2) span").textContent = data.email;

            let dateStr = data.signup_date;
            let date = new Date(dateStr);
            let year = date.getFullYear();
            let month = String(date.getMonth() + 1).padStart(2, '0');
            let day = String(date.getDate()).padStart(2, '0');
            let formattedDate = `${year}-${month}-${day}`;
            document.querySelector(".profile-section .profile-item:nth-child(3) span").textContent = formattedDate;

            const activitySection = document.querySelector(".profile-section + .profile-section ul");
            activitySection.innerHTML = `
                <li>작성한 메모: ${data.notes_count}개</li>
                <li>완료한 퀴즈: ${data.quizzes_completed}개</li>
                <li>받은 피드백: ${data.feedback_received}개</li>
            `;
        })
        .catch(error => {
            console.error(error);
            alert("유저 정보를 불러오는 중 오류가 발생했습니다.");
        });
}
