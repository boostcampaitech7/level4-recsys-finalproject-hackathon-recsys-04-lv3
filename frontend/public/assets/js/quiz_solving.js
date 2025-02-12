// quiz_solving.js
let currentQuiz = null;
let questionIndex = 0;

window.onload = async function () {
    const userId = localStorage.getItem("user_id");
    const noteId = localStorage.getItem("current_note_id");

    if (!userId || !noteId) {
        alert("필요한 정보가 없습니다.");
        window.location.href = "quiz.html";
        return;
    }

    await loadQuiz(userId, noteId);
};

async function loadQuiz(userId, noteId) {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/quiz/next?user_id=${userId}&note_id=${noteId}`);
        if (!response.ok) {
            throw new Error("Failed to fetch quiz");
        }

        const data = await response.json();
        const quiz = data.quiz;
        displayQuestion(quiz);
    } catch (error) {
        console.error("Error loading quiz:", error);
        alert("퀴즈를 불러오는데 실패했습니다.");
        window.location.href = "quiz.html";
    }
}

function displayQuestion(quiz) {
    currentQuiz = quiz;
    document.getElementById('question-text').textContent = quiz.question;
    document.getElementById('explanation').style.display = 'none';
    document.getElementById('next-btn').style.display = 'none';

    document.querySelectorAll('.answer').forEach(el => {
        el.classList.remove('unselected');
        el.style.pointerEvents = 'auto';
    });

    updateProgressDot();

    if (questionIndex === 4) {
        document.getElementById('next-btn').textContent = "결과 확인하기";
    }
}

async function selectAnswer(choice) {
    const answers = document.querySelectorAll('.answer');
    answers.forEach(el => {
        el.classList.add('unselected');
        el.style.pointerEvents = 'none';
    });
    document.querySelector(`.answer.${choice.toLowerCase()}`).classList.remove('unselected');

    const userId = localStorage.getItem("user_id");
    const noteId = localStorage.getItem("current_note_id");

    try {
        const formData = new FormData();
        formData.append("user_id", userId);
        formData.append("ox_id", currentQuiz.ox_id);
        formData.append("user_answer", choice);

        const response = await fetch(`http://localhost:8000/api/v1/quiz/solve`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to submit answer");
        }

        const data = await response.json();
        displayResult(data.result);
    } catch (error) {
        console.error("Error submitting answer:", error);
        alert("답변 제출에 실패했습니다.");
    }
}

function displayResult(result) {
    document.getElementById('result').innerText = result.is_correct;
    document.getElementById('detail').innerText = result.explanation;
    document.getElementById('explanation').style.display = 'block';
    document.getElementById('next-btn').style.display = 'block';
}

async function nextQuestion() {
    const userId = localStorage.getItem("user_id");
    const noteId = localStorage.getItem("current_note_id");

    if (questionIndex < 4) {
        questionIndex++;
        await loadQuiz(userId, noteId);
    } else {
        window.location.href = "quiz_result.html";
    }
}

function updateProgressDot() {
    const progressDots = document.querySelectorAll('.progress-dot');
    progressDots.forEach((dot, index) => {
        dot.style.backgroundColor = index <= questionIndex ? '#007BFF' : '#E9ECEF';
    });
}
