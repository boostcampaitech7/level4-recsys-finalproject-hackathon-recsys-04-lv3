// feedback.js
document.addEventListener('DOMContentLoaded', () => {
    loadFeedback();
});

async function loadFeedback() {
    try {
        const userId = localStorage.getItem('user_id');
        if (!userId) {
            window.location.href = 'login.html';
            return;
        }

        const [feedbackResponse, quizzesResponse] = await Promise.all([
            fetch(`http://localhost:8000/api/v1/user/${userId}/feedbacks`),
            fetch(`http://localhost:8000/api/v1/user/${userId}/quizzes`)
        ]);

        const feedbackData = await feedbackResponse.json();
        const quizData = await quizzesResponse.json();

        console.log('Feedback Data:', feedbackData);
        console.log('Quiz Data:', quizData);

        renderFeedbacks(feedbackData.feedbacks || []);
        renderQuizzes(quizData.quizzes || []); // quizData.quizzes로 수정
    } catch (error) {
        console.error('데이터 로드 오류:', error);
        showError('데이터를 불러오는데 실패했습니다.');
    }
}

function renderFeedbacks(feedbacks) {
    const feedbackList = document.querySelector('.feedback-list');
    feedbackList.innerHTML = '';

    if (!feedbacks || feedbacks.length === 0) {
        const li = document.createElement('li');
        li.className = 'feedback-item';
        li.textContent = '받은 피드백이 없습니다.';
        feedbackList.appendChild(li);
        return;
    }

    feedbacks.forEach(feedback => {
        const li = document.createElement('li');
        li.className = 'feedback-item';
        const title = feedback.note_title || '제목 없음';
        const content = feedback.feedback || '내용 없음';
        li.textContent = `${title}: ${content}`;
        feedbackList.appendChild(li);
    });
}

function renderQuizzes(quizzes) {
    const quizFeedbackList = document.querySelectorAll('.feedback-list')[1];
    quizFeedbackList.innerHTML = '';

    // 답변이 있는 퀴즈만 필터링
    const answeredQuizzes = quizzes.filter(quiz => quiz.answer || quiz.ox_answer);

    if (answeredQuizzes.length === 0) {
        quizFeedbackList.innerHTML = '<li class="feedback-item">푼 퀴즈가 없습니다.</li>';
        return;
    }

    const quizItems = answeredQuizzes.map(quiz => `
        <li class="feedback-item">
            문제: ${quiz.question || quiz.ox_contents}
            <br>
            선택: ${quiz.answer || quiz.ox_answer},
            정답여부: ${quiz.correct_yn === 'Y' ? '정답' : '오답'}
        </li>
    `).join('');

    quizFeedbackList.innerHTML = quizItems;
 }

function showError(message) {
    const mainContent = document.getElementById('main-content');
    const existingError = mainContent.querySelector('.error-message');

    if (existingError) {
        existingError.remove();
    }

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    mainContent.prepend(errorDiv);
}
