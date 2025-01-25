// public/assets/js/quiz.js
document.addEventListener('DOMContentLoaded', function() {
    const userId = localStorage.getItem("user_id");
    const noteId = localStorage.getItem("current_note_id");

    if (!userId) {
        alert("로그인이 필요합니다.");
        window.location.href = "login.html";
    }
});

// 퀴즈 페이지 이동 함수
function goToQuizSolving() {
    const noteId = localStorage.getItem("current_note_id");
    if (!noteId) {
        alert("노트를 선택해주세요.");
        window.location.href = "notes.html";
        return;
    }
    window.location.href = "quiz_solving.html";
}
