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
            `${SERVER_BASE_URL}/api/v1/quiz/history?user_id=${userId}`,
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
        displayQuizHistory(data.quizzes);
    } catch (error) {
        console.error('Error loading quiz history:', error);
        alert('퀴즈 기록을 불러오는데 실패했습니다.');
    }
}

function displayQuizHistory(quizzes) {
    const historyList = document.getElementById('quiz-history-list');
    const totalCount = quizzes.length;
    const correctCount = quizzes.filter(quiz => quiz.correct_yn === 'Y').length;
    const correctRate = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

    // 통계 업데이트
    document.getElementById('total-count').textContent = `${totalCount}개`;
    document.getElementById('correct-rate').textContent = `${correctRate}%`;

    // 퀴즈 기록 표시
    historyList.innerHTML = quizzes.map(quiz => {
        const getOptionClass = (optionNumber) => {
            const isUserAnswer = quiz.user_answer === optionNumber;
            const isCorrectAnswer = quiz.answer === optionNumber;

            if (isUserAnswer && !isCorrectAnswer) {
                return 'incorrect-answer';  // 사용자가 선택한 오답 (빨간색)
            }
            if (isCorrectAnswer) {
                return 'correct-answer';  // 정답 (초록색)
            }
            if (isUserAnswer) {
                return 'user-answer';  // 사용자가 선택한 답 (기본)
            }
            return '';  // 나머지 선택지
        };

        return `
        <div class="quiz-history-item ${quiz.correct_yn === 'Y' ? 'correct' : 'incorrect'}">
            <div class="quiz-content">
                <h3>${quiz.question}</h3>
                <div class="quiz-options">
                    <div class="option ${getOptionClass('1')}">${quiz.options['1']}</div>
                    <div class="option ${getOptionClass('2')}">${quiz.options['2']}</div>
                    <div class="option ${getOptionClass('3')}">${quiz.options['3']}</div>
                    <div class="option ${getOptionClass('4')}">${quiz.options['4']}</div>
                </div>
                <div class="quiz-result">
                    <p class="${quiz.correct_yn === 'Y' ? 'correct-text' : 'incorrect-text'}">
                        ${quiz.correct_yn === 'Y' ? '정답입니다!' : '틀렸습니다.'}
                    </p>
                    <p>정답: ${quiz.answer}번</p>
                    ${quiz.correct_yn === 'N' ? `<p>선택한 답: ${quiz.user_answer}번</p>` : ''}
                </div>
                <p class="quiz-explanation">${quiz.explanation || ''}</p>
            </div>
            <div class="quiz-date">${quiz.solved_at}</div>
        </div>`;
    }).join('');
}

async function loadSubjectResetButtons(userId) {
    try {
        // 과목 목록 가져오기
        const response = await fetch(`${SERVER_BASE_URL}/api/v1/note/subjects?user_id=${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch subjects');
        }

        const data = await response.json();
        const buttonContainer = document.getElementById('subject-reset-buttons');
        buttonContainer.innerHTML = '';

        // 각 과목별 리셋 버튼 생성
        data.subjects.forEach(subject => {
            const button = document.createElement('button');
            button.className = 'btn btn-secondary';
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
        formData.append("quiz_type", "multiple");  // multiple 퀴즈만 리셋하도록 추가
        if (subject) {
            formData.append("subject_id", subject);
        }

        const response = await fetch(`${SERVER_BASE_URL}/api/v1/quiz/reset`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.text();
            console.error('Server error:', errorData);
            throw new Error("Failed to reset quizzes");
        }

        const result = await response.json();

        alert(subject ?
            `${subject} 과목의 퀴즈가 리셋되었습니다.` :
            "모든 퀴즈가 리셋되었습니다."
        );

        // 페이지 이동 대신 현재 페이지에서 버튼 상태 갱신
        location.reload();  // 현재 페이지 새로고침
    } catch (error) {
        console.error("Error resetting quizzes:", error);
        alert("퀴즈 리셋에 실패했습니다.");
    }
}

async function resetAllQuizzes() {
    // subject 파라미터 없이 resetQuizzes 호출
    await resetQuizzes();
}
