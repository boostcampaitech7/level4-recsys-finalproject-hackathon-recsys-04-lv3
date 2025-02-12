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
    if (!userId) {
        alert("로그인이 필요합니다.");
        window.location.href = "index.html";
        return;
    }
    window.location.href = "quiz_solving_multiple.html";
}

function goToMultipleQuizHistory() {
    window.location.href = "quiz_history.html";
}

function goToOXQuizHistory() {
    window.location.href = "ox_quiz_history.html";
}
