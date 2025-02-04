document.addEventListener('DOMContentLoaded', () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    loadFeedback();
});

async function loadFeedback() {
    const feedbackLists = document.querySelectorAll('.feedback-list');

    // 로딩 상태 표시
    feedbackLists.forEach(list => {
        list.innerHTML = `
            <li class="loading">
                <div class="loading-spinner"></div>
                <p>피드백을 불러오는 중...</p>
            </li>
        `;
    });

    try {
        const userId = localStorage.getItem('user_id');
        const [feedbackResponse, quizzesResponse] = await Promise.all([
            fetchWithTimeout(`http://localhost:8000/api/v1/user/${userId}/feedbacks`),
            fetchWithTimeout(`http://localhost:8000/api/v1/user/${userId}/quizzes`)
        ]);

        const [feedbackData, quizData] = await Promise.all([
            feedbackResponse.json(),
            quizzesResponse.json()
        ]);

        renderFeedbacks(feedbackData.feedbacks || []);
        renderQuizzes(quizData.quizzes || []);
    } catch (error) {
        console.error('데이터 로드 오류:', error);
        showError(error.message === 'timeout'
            ? '서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.'
            : '데이터를 불러오는데 실패했습니다.');
    }
}

function fetchWithTimeout(url, timeout = 5000) {
    return Promise.race([
        fetch(url),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('timeout')), timeout)
        )
    ]);
}

function renderFeedbacks(feedbacks) {
    const feedbackList = document.querySelector('.feedback-list');

    if (!feedbacks || feedbacks.length === 0) {
        feedbackList.innerHTML = `
            <li class="empty-state">
                <p>아직 받은 피드백이 없습니다.</p>
            </li>
        `;
        return;
    }

    feedbackList.innerHTML = feedbacks
        .map(feedback => {
            const title = escapeHtml(feedback.note_title || '제목 없음');
            const content = escapeHtml(feedback.feedback || '내용 없음');
            const date = formatDate(feedback.created_at);
            const subject = escapeHtml(feedback.subject || '')

            return `
                <li class="feedback-item">
                    <div class="feedback-header">
                        <strong>${title}</strong>
                        <br>
                        <span >${subject}</span>
                        <span class="feedback-date">| ${date}</span>
                    </div>
                    <pre class="feedback-content">${content}</pre>
                </li>
            `;
        })
        .join('');
}

function renderQuizzes(quizzes) {
    const quizList = document.querySelectorAll('.feedback-list')[1];

    const answeredQuizzes = quizzes.filter(quiz => quiz.is_correct);

    if (!answeredQuizzes || answeredQuizzes.length === 0) {
        quizList.innerHTML = `
            <li class="empty-state">
                <p>아직 푼 OX 퀴즈가 없습니다.</p>
            </li>
        `;
        return;
    }

    quizList.innerHTML = answeredQuizzes.map(quiz => {
        const isCorrect = quiz.is_correct === 'Y';
        const resultText = isCorrect ? '정답입니다' : '오답입니다';
        const itemClass = isCorrect ? 'correct' : 'incorrect';

        return `
            <li class="feedback-item ${itemClass}">
                <span class="result-badge ${itemClass}">
                    ${resultText}
                </span>

                <div class="quiz-question">
                    ${escapeHtml(quiz.question)}
                </div>

                <div class="answers-grid">
                    <div class="answer-row">
                        <div class="answer-label">내가 제출한 답</div>
                        <div class="answer-value">
                            <span class="answer-circle">${quiz.answer}</span>
                        </div>
                    </div>

                    <div class="answer-row">
                        <div class="answer-label">정답</div>
                        <div class="answer-value">
                            <span class="answer-circle">${quiz.answer}</span>
                        </div>
                    </div>
                </div>

                ${quiz.explanation ? `
                    <div class="explanation">
                        ${escapeHtml(quiz.explanation)}
                    </div>
                ` : ''}
            </li>
        `;
    }).join('');
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showError(message) {
    const mainContent = document.getElementById('main-content');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <p>${message}</p>
        <button onclick="loadFeedback()" class="retry-btn">
            다시 시도
        </button>
    `;
    mainContent.prepend(errorDiv);
}
