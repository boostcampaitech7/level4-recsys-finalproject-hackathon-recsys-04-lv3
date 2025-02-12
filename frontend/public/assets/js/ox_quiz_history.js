const SERVER_BASE_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', async function() {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
        alert("로그인이 필요합니다.");
        window.location.href = "index.html";
        return;
    }

    await loadQuizHistory(userId);
    await loadSubjectResetButtons(userId);
});

async function loadQuizHistory(userId) {
    try {
        const response = await fetch(
            `${SERVER_BASE_URL}/api/v1/user/${userId}/quizzes`,
            {
                headers: {
                    'Accept': 'application/json'
                }
            }
        );

        if (!response.ok) {
            throw new Error('Failed to fetch quiz history');
        }

        const data = await response.json();
        console.log('OX 퀴즈 데이터:', data.quizzes);
        displayOXQuizHistory(data.quizzes || []);
    } catch (error) {
        console.error('Error loading quiz history:', error);
        alert('퀴즈 기록을 불러오는데 실패했습니다.');
    }
}

function displayOXQuizHistory(quizzes) {
    const historyList = document.getElementById('quiz-history-list');
    const answeredQuizzes = quizzes.filter(quiz => quiz.answer !== null);

    updateStatistics(answeredQuizzes);

    if (!answeredQuizzes || answeredQuizzes.length === 0) {
        historyList.innerHTML = `
            <div class="feedback-item empty-state">
                <p>아직 푼 OX 퀴즈가 없습니다.</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = answeredQuizzes.map(quiz => {
        const isCorrect = quiz.is_correct === 'Y';
        const correctAnswer = isCorrect ? quiz.answer : (quiz.answer === 'O' ? 'X' : 'O');

        return `
            <div class="feedback-item ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="quiz-question">
                    ${escapeHtml(quiz.question)}
                </div>

                <div class="quiz-answer">
                    <span class="answer-label">내가 체크한 답:</span>
                    <span class="answer-value ${isCorrect ? 'correct' : 'incorrect'}">${quiz.answer}</span>
                </div>

                <div class="quiz-answer">
                    <span class="answer-label">정답:</span>
                    <span class="answer-value correct">${correctAnswer}</span>
                </div>

                ${quiz.explanation ? `
                    <div class="quiz-explanation">
                        ${escapeHtml(quiz.explanation)}
                    </div>
                ` : ''}

                <div class="quiz-date">
                    ${new Date(quiz.created_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    })}
                </div>
            </div>
        `;
    }).join('');
}

function updateStatistics(quizzes) {
    const totalCount = quizzes.length;
    const correctCount = quizzes.filter(quiz => quiz.is_correct === 'Y').length;
    const correctRate = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

    document.getElementById('total-count').textContent = `${totalCount}개`;
    document.getElementById('correct-rate').textContent = `${correctRate}%`;
}

// 나머지 함수들은 그대로 유지
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function loadSubjectResetButtons(userId) {
    try {
        const response = await fetch(`${SERVER_BASE_URL}/api/v1/note/subjects?user_id=${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch subjects');
        }

        const data = await response.json();
        const buttonContainer = document.getElementById('subject-reset-buttons');
        buttonContainer.innerHTML = '';

        data.subjects.forEach(subject => {
            const button = document.createElement('button');
            button.textContent = `${subject} 다시풀기`;
            button.onclick = () => resetQuizzes(subject);
            buttonContainer.appendChild(button);
        });
    } catch (error) {
        console.error('Error loading subjects:', error);
    }
}

async function resetQuizzes(subject = null) {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    try {
        const formData = new FormData();
        formData.append("user_id", userId);
        formData.append("quiz_type", "ox");
        if (subject) {
            formData.append("subject_id", subject);
        }

        const response = await fetch(`${SERVER_BASE_URL}/api/v1/quiz/reset`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to reset quizzes");
        }

        await response.json();
        alert(subject ?
            `${subject} 과목의 OX 퀴즈가 리셋되었습니다.` :
            "모든 OX 퀴즈가 리셋되었습니다."
        );

        location.reload();
    } catch (error) {
        console.error("Error resetting quizzes:", error);
        alert("퀴즈 리셋에 실패했습니다.");
    }
}

async function resetAllQuizzes() {
    await resetQuizzes();
}
