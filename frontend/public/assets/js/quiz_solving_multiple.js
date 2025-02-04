const SERVER_BASE_URL = 'http://localhost:8000';
let currentQuiz = null;
let questionIndex = 0;
let currentSubject = null;
let currentQuizzes = [];

document.addEventListener('DOMContentLoaded', async function() {
   const userId = localStorage.getItem("user_id");

   if (!userId) {
       alert("로그인이 필요합니다.");
       window.location.href = "index.html";
       return;
   }

   await loadSubjects(userId);
});

async function loadSubjects(userId) {
   try {
       const response = await fetch(`${SERVER_BASE_URL}/api/v1/note/subjects?user_id=${userId}`);
       if (!response.ok) {
           throw new Error('Failed to fetch subjects');
       }

       const data = await response.json();
       const subjectsList = document.getElementById('subjects-list');
       subjectsList.innerHTML = '';

       data.subjects.forEach(subject => {
           const button = document.createElement('button');
           button.className = 'subject-button';
           button.textContent = subject;
           button.onclick = () => selectSubject(subject);
           subjectsList.appendChild(button);
       });
   } catch (error) {
       console.error('Error loading subjects:', error);
       alert('과목 목록을 불러오는데 실패했습니다.');
   }
}

async function selectSubject(subjectId) {
    currentSubject = subjectId;
    const userId = localStorage.getItem("user_id");

    try {
        const encodedSubject = encodeURIComponent(subjectId);
        const response = await fetch(
            `${SERVER_BASE_URL}/api/v1/quiz/multiple/by-subject/${encodedSubject}?user_id=${userId}`
        );

        if (!response.ok) {
            throw new Error('Failed to fetch quizzes');
        }

        const data = await response.json();

        // 모든 문제를 풀었을 경우
        if (data.message) {
            alert(data.message);
            if (data.redirect) {
                window.location.href = 'quiz_history.html';  // 퀴즈 히스토리 페이지로 리다이렉트
            }
            return;
        }

        currentQuizzes = data.quizzes;

        // UI 전환
        document.getElementById('subject-selection').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';

        // 첫 문제 표시
        questionIndex = 0;
        displayQuestion(currentQuizzes[0]);
    } catch (error) {
        console.error('Error loading quizzes:', error);
        alert('퀴즈를 불러오는데 실패했습니다.');
    }
}

function displayQuestion(quiz) {
    currentQuiz = quiz;

    document.getElementById('question-text').textContent = quiz.question;

    const optionButtons = document.querySelectorAll('.option');
    optionButtons.forEach((button, index) => {
        const optionNumber = index + 1;
        button.textContent = quiz[`option${optionNumber}`];
        button.classList.remove('selected', 'correct', 'incorrect');
        button.disabled = false;
    });

    document.getElementById('explanation').style.display = 'none';
    document.getElementById('next-btn').style.display = 'none';
    document.getElementById('back-to-subjects').style.display = 'none';

    updateProgress();
 }

async function selectAnswer(choice) {
   if (!currentQuiz) return;

   const userId = localStorage.getItem("user_id");
   if (!userId) return;

   const formData = new FormData();
   formData.append("user_id", userId);
   formData.append("quiz_id", currentQuiz.quiz_id);
   formData.append("user_answer", choice);

   try {
       const response = await fetch(`${SERVER_BASE_URL}/api/v1/quiz/solve/multiple`, {
           method: "POST",
           body: formData
       });

       if (!response.ok) {
           throw new Error("Failed to submit answer");
       }

       const data = await response.json();
       displayResult(data.result, choice);
   } catch (error) {
       console.error("Error submitting answer:", error);
       alert("답변 제출에 실패했습니다.");
   }
}

function displayResult(result, userChoice) {
    const options = document.querySelectorAll('.option');
    options.forEach(option => option.disabled = true);

    const correctOption = document.querySelector(`[data-option="${result.correct_answer}"]`);
    const selectedOption = document.querySelector(`[data-option="${userChoice}"]`);

    if (correctOption) correctOption.classList.add('correct');
    if (selectedOption && userChoice !== result.correct_answer) {
        selectedOption.classList.add('incorrect');
    }

    document.getElementById('result').innerText = result.is_correct;
    document.getElementById('detail').innerText = result.explanation;
    document.getElementById('explanation').style.display = 'block';
    document.getElementById('next-btn').style.display = 'block';
}

function nextQuestion() {
    if (questionIndex < currentQuizzes.length - 1) {
        questionIndex++;
        displayQuestion(currentQuizzes[questionIndex]);
    } else {
        // 모든 문제를 다 풀었을 때 히스토리 페이지로 이동
        window.location.href = 'quiz_history.html';
    }
}

function backToSubjects() {
   document.getElementById('quiz-container').style.display = 'none';
   document.getElementById('subject-selection').style.display = 'block';
   currentQuiz = null;
   questionIndex = 0;
   currentQuizzes = [];
}

function updateProgress() {
    const totalQuestions = currentQuizzes.length;
    const currentNumber = questionIndex + 1;
    const percentage = (currentNumber / totalQuestions) * 100;

    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.innerHTML = `
        <div class="progress-fill" style="width: ${percentage}%"></div>
    `;

    const progressText = document.createElement('div');
    progressText.className = 'progress-text';
    progressText.textContent = `${currentNumber} / ${totalQuestions}`;

    const progressContainer = document.querySelector('.progress-container');
    progressContainer.innerHTML = '';
    progressContainer.appendChild(progressBar);
    progressContainer.appendChild(progressText);
}
