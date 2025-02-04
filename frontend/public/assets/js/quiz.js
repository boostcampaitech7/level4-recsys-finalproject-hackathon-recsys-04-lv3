// quiz.js
document.addEventListener('DOMContentLoaded', function() {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
        alert("로그인이 필요합니다.");
        window.location.href = "index.html";
        return;
    }
});

function goToQuizSolving() {
    const userId = localStorage.getItem("user_id");
    const noteId = localStorage.getItem("current_note_id");

    if (!userId) {
        alert("로그인이 필요합니다.");
        window.location.href = "index.html";
        return;
    }

    // 노트 ID 체크를 여기서는 하지 않습니다
    window.location.href = "quiz_solving_multiple.html";
}

function goToQuizHistory() {
    window.location.href = "quiz_history.html";
}
