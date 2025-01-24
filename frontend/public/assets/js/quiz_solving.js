let currentQuiz = null; // 현재 퀴즈 정보 저장
let questionIndex = 0;  // 문제 인덱스 (0: 첫 번째 문제, 1: 두 번째 문제, 2: 세 번째 문제)

// 페이지 로드 시 첫 번째 퀴즈 가져오기
window.onload = async function () {
    try {
        // 로그인된 유저 아이디 가져오기
        const userId = localStorage.getItem("user_id");  // localStorage에 저장된 user_id 가져오기

        if (!userId) {
            alert("로그인된 유저가 없습니다.");
            return;
        }

        // 첫 번째 퀴즈 데이터 가져오기
        await loadQuiz(userId);
    } catch (error) {
        console.error("Error loading quiz:", error);
        alert("퀴즈를 가져오는데 실패했습니다.");
    }
};

async function loadQuiz(userId) {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/quiz/next?user_id=${userId}`);
        if (!response.ok) {
            throw new Error("Failed to fetch quiz");
        }

        const data = await response.json(); // JSON 데이터 파싱
        const quiz = data.quiz; // 퀴즈 데이터 추출

        // 퀴즈 표시
        displayQuestion(quiz);
    } catch (error) {
        console.error("Error loading quiz:", error);
        alert("퀴즈를 가져오는데 실패했습니다.");
    }
}

function displayQuestion(quiz) {
    // API에서 가져온 질문과 데이터를 화면에 표시
    currentQuiz = quiz; // 현재 퀴즈 데이터 저장
    const questionBox = document.getElementById('question-text');
    questionBox.textContent = quiz.question; // 질문 텍스트 설정

    document.getElementById('explanation').style.display = 'none'; // 해설 숨기기
    document.getElementById('next-btn').style.display = 'none'; // 다음 버튼 숨기기

    // 선택 상태 초기화
    document.querySelectorAll('.answer').forEach(el => el.classList.remove('unselected'));

    // progress-dot 업데이트
    updateProgressDot();

    // 마지막 문제라면 "결과 확인하러 가기" 버튼 표시
    if (questionIndex === 2) {
        document.getElementById('next-btn').textContent = "결과 확인하러 가기";
    }
}

// 사용자가 답을 선택했을 때 처리
async function selectAnswer(choice) {
    // 선택한 답을 강조
    document.querySelectorAll('.answer').forEach(el => el.classList.add('unselected'));
    document.querySelector(`.answer.${choice.toLowerCase()}`).classList.remove('unselected');

    // 로그인된 유저 아이디 가져오기
    const userId = localStorage.getItem("user_id");  // 로컬 스토리지에 저장된 user_id 사용

    if (!userId) {
        alert("로그인된 유저가 없습니다.");
        return;
    }

    try {
        // FastAPI에 사용자가 선택한 답 제출
        const response = await fetch(`http://localhost:8000/api/v1/quiz/solve?user_id=${userId}&ox_id=${currentQuiz.ox_id}&user_answer=${choice}`, {
            method: "POST",  // 쿼리 파라미터를 URL에 포함시킨다.
            headers: {
                "Content-Type": "application/json",  // 요청 헤더 설정
            },
        });

        if (!response.ok) {
            throw new Error("Failed to submit answer");
        }

        const data = await response.json(); // 결과 데이터 파싱
        displayResult(data.result); // 결과 표시
    } catch (error) {
        console.error("Error submitting answer:", error);
        alert("답변 제출에 실패했습니다.");
    }
}

function displayResult(result) {
    // 결과와 해설 표시
    document.getElementById('result').innerText = result.is_correct;
    document.getElementById('detail').innerText = result.explanation;
    document.getElementById('explanation').style.display = 'block';

    // 다음 버튼 표시
    document.getElementById('next-btn').style.display = 'block';
}

// 다음 문제로 이동
async function nextQuestion() {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
        alert("로그인된 유저가 없습니다.");
        return;
    }

    if (questionIndex < 2) {
        questionIndex++; // 문제 인덱스 증가
        await loadQuiz(userId); // 다음 퀴즈 로드
    } else {
        // 마지막 문제에서는 결과 페이지로 이동
        window.location.href = "quiz_result.html";
    }
}

// progress-dot 업데이트
function updateProgressDot() {
    const progressDots = document.querySelectorAll('.progress-dot');
    progressDots.forEach((dot, index) => {
        if (index <= questionIndex) {
            dot.classList.add('filled');
        } else {
            dot.classList.remove('filled');
        }
    });
}
