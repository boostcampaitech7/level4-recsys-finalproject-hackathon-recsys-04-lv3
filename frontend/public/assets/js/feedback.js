// feedback.js
document.addEventListener('DOMContentLoaded', () => {
    loadFeedback();
});

async function loadFeedback() {
    try {
        const userId = localStorage.getItem('user_id');
        if (!userId) {
            window.location.href = '/login.html';
            return;
        }

        // 피드백 가져오기
        const feedbackResponse = await fetch(`/api/v1/user/${userId}/feedbacks`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const feedbacks = await feedbackResponse.json();

        // 퀴즈 결과 가져오기
        const quizzesResponse = await fetch(`/api/v1/user/${userId}/quizzes`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const quizzes = await quizzesResponse.json();

        renderFeedbacks(feedbacks);
        renderQuizzes(quizzes);
    } catch (error) {
        console.error('데이터를 불러오는 중 오류가 발생했습니다:', error);
        showError('데이터를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.');
    }
}

function renderFeedbacks(feedbacks) {
    const feedbackList = document.querySelector('.feedback-list');
    feedbackList.innerHTML = '';

    feedbacks.forEach(feedback => {
        const li = document.createElement('li');
        li.className = 'feedback-item';
        li.textContent = `${feedback.note_title}: ${feedback.content}`;
        feedbackList.appendChild(li);
    });
}

function renderQuizzes(quizzes) {
    const quizFeedbackList = document.querySelectorAll('.feedback-list')[1];
    quizFeedbackList.innerHTML = '';

    quizzes.forEach(quiz => {
        const li = document.createElement('li');
        li.className = 'feedback-item';
        li.textContent = `문제 ${quiz.quiz_number}: ${quiz.is_correct ? '정답' : '오답'} (${quiz.user_answer})`;
        quizFeedbackList.appendChild(li);
    });
}

function showError(message) {
    const mainContent = document.getElementById('main-content');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    mainContent.prepend(errorDiv);
}
