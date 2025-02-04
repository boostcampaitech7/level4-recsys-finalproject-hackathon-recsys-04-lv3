const urlParams = new URLSearchParams(window.location.search);
const noteId = urlParams.get("note_id");
const userId = localStorage.getItem("user_id");
const SERVER_BASE_URL = 'http://127.0.0.1:8000';

async function fetchNoteData() {
    try {
        // 초기 로딩 상태 설정
        const imageContainer = document.querySelector('.note-box.image');
        const feedbackContainer = document.querySelector('.note-box.feedback');
        const quizContainer = document.querySelector('.note-box.recommendation');

        // API 호출
        const [noteResponse, quizResponse] = await Promise.all([
            fetch(`${SERVER_BASE_URL}/api/v1/note/?note_id=${noteId}&user_id=${userId}`),
            fetch(`${SERVER_BASE_URL}/api/v1/quiz/next?user_id=${userId}&note_id=${noteId}`)
        ]);

        if (!noteResponse.ok || !quizResponse.ok) {
            throw new Error('API 요청 실패');
        }

        const noteData = await noteResponse.json();
        const quizData = await quizResponse.json();

        // 기본 정보 표시
        document.getElementById('note-title').textContent = noteData.title;
        document.getElementById('subject-name').textContent = `과목: ${noteData.subjects_id}`;
        document.getElementById('note-date').textContent = formatDate(noteData.note_date);
        document.querySelector('.feedback').innerHTML = `<pre><h3>피드백</h3><p>${noteData.feedback || '피드백이 없습니다'}</p></pre>`;

        // 이미지/콘텐츠 렌더링
        if (noteData.file_path) {
            imageContainer.innerHTML = '';
            const fileName = noteData.file_path.split(/[\/\\]/).pop();
            const fileUrl = `${SERVER_BASE_URL}/uploads/${fileName}`;
            const fileExtension = fileName.split('.').pop().toLowerCase();

            if (fileExtension === 'pdf') {
                const pdfViewer = document.createElement('iframe');
                pdfViewer.src = fileUrl;
                pdfViewer.style.width = '100%';
                pdfViewer.style.height = '100%';
                pdfViewer.style.border = 'none';
                imageContainer.appendChild(pdfViewer);
            } else {
                const img = document.createElement('img');
                img.src = fileUrl;
                img.alt = '노트 이미지';
                img.style.maxWidth = '100%';

                img.onload = () => {
                    // 이미지 로드 완료 후 애니메이션 시작
                    imageContainer.classList.add('active');
                };

                img.onerror = () => {
                    console.error('이미지 로드 실패:', fileUrl);
                    imageContainer.textContent = '이미지를 불러올 수 없습니다.';
                    imageContainer.classList.add('active');
                };

                imageContainer.appendChild(img);
            }
        } else if (noteData.raw_text) {
            const textElement = document.createElement('pre');
            textElement.textContent = noteData.raw_text;
            textElement.style.whiteSpace = 'pre-wrap';
            imageContainer.appendChild(textElement);
            imageContainer.classList.add('active');
        }

        // 0.2초 후 피드백과 퀴즈 표시
        setTimeout(() => {
            // 피드백 렌더링
            feedbackContainer.innerHTML = `
                <h3>피드백</h3>
                <p>${noteData.feedback || '피드백이 없습니다'}</p>
            `;
            feedbackContainer.classList.add('active');

            // 퀴즈 렌더링
            if (quizData.quiz) {
                quizContainer.innerHTML = `
                    <h3>OX 퀴즈</h3>
                    <div class="quiz-item">
                        <p>${quizData.quiz.question}</p>
                        <div class="quiz-buttons">
                            <button onclick="solveQuiz('O', '${quizData.quiz.ox_id}')">O</button>
                            <button onclick="solveQuiz('X', '${quizData.quiz.ox_id}')">X</button>
                        </div>
                    </div>
                `;
            } else {
                quizContainer.innerHTML = `
                    <div class="quiz-item">
                        <h3>OX 퀴즈</h3>
                        <p>${quizData.message || '모든 OX 퀴즈를 풀었습니다!'}</p>
                        <button onclick="resetQuizzes()" class="reset-quiz-btn">퀴즈 다시 풀기</button>
                    </div>
                `;
            }
            quizContainer.classList.add('active');
        }, 200);

    } catch (error) {
        console.error('Error:', error);
        document.querySelector('.recommendation').innerHTML = `
            <div class="quiz-item">
                <p>퀴즈를 불러오는데 실패했습니다.</p>
                <button onclick="fetchNoteData()" class="retry-btn">다시 시도</button>
            </div>
        `;
    }
}

async function resetQuizzes() {
    try {
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('note_id', noteId);
        formData.append('quiz_type', 'ox');  // OX 퀴즈만 리셋

        const response = await fetch(`${SERVER_BASE_URL}/api/v1/quiz/reset`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('퀴즈 리셋 실패');

        // 리셋 성공 후 퀴즈 다시 불러오기
        fetchNoteData();
    } catch (error) {
        console.error('Error resetting quizzes:', error);
        document.querySelector('.recommendation').innerHTML = `
            <div class="quiz-item">
                <p>퀴즈 리셋에 실패했습니다.</p>
                <button onclick="resetQuizzes()" class="retry-btn">다시 시도</button>
            </div>
        `;
    }
}

async function solveQuiz(answer, oxId) {
    try {
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('ox_id', oxId);
        formData.append('user_answer', answer);

        const response = await fetch(`${SERVER_BASE_URL}/api/v1/quiz/solve`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Failed to submit answer');

        const result = await response.json();
        displayQuizResult(result);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayQuizResult(result) {
    const isCorrect = result.result.is_correct === "정답입니다!";
    const resultHtml = `
        <div class="quiz-result ${isCorrect ? 'correct' : 'incorrect'} fade-in">
            <span class="result-badge ${isCorrect ? 'correct' : 'incorrect'}">
                ${isCorrect ? '정답' : '오답'}
            </span>
            <p>${result.result.is_correct}</p>
            <p>정답: ${result.result.correct_answer}</p>
            <p class="explanation ${isCorrect ? 'correct' : 'incorrect'}">해설: ${result.result.explanation}</p>
            <button onclick="fetchNoteData()" class="next-quiz-btn ${isCorrect ? 'correct' : 'incorrect'}">
                다음 문제
            </button>
        </div>
    `;
    const quizContainer = document.querySelector('.recommendation');
    quizContainer.innerHTML = resultHtml;
    // 결과 표시 후 애니메이션 적용
    setTimeout(() => {
        quizContainer.querySelector('.quiz-result').classList.add('active');
    }, 10);
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    date.setHours(date.getHours() + 9); // KST 시간대 조정
    return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;
}

document.addEventListener('DOMContentLoaded', fetchNoteData);
