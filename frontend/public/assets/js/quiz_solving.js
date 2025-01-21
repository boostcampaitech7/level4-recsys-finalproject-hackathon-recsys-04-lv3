let currentQuestion = 0;
const questions = [
    { text: "태양은 지구를 중심으로 돈다.", answer: "X", explanation: "태양을 중심으로 지구가 돌아요" },
    { text: "물은 100도에서 끓는다.", answer: "O", explanation: "물은 100도에서 끓어요." },
    { text: "지구는 평평하다.", answer: "X", explanation: "지구는 둥글어요." }
];

function selectAnswer(choice) {
    document.querySelectorAll('.answer').forEach(el => el.classList.add('unselected'));
    document.querySelector(`.answer.${choice.toLowerCase()}`).classList.remove('unselected');

    const correct = questions[currentQuestion].answer;
    document.getElementById('result').innerText = (choice === correct) ? "정답이에요!" : "오답이에요!";
    document.getElementById('detail').innerText = questions[currentQuestion].explanation;
    document.getElementById('explanation').style.display = 'block';
    document.getElementById('next-btn').style.display = 'block';

    document.querySelectorAll('.progress-dot')[currentQuestion].classList.add('active');

    if (currentQuestion === questions.length - 1) {
        document.getElementById('next-btn').innerText = '결과 확인하러 가기';
        document.getElementById('next-btn').setAttribute('onclick', "location.href='quiz_result.html'");
    }
}

function nextQuestion() {
    currentQuestion++;
    if (currentQuestion < questions.length) {
        document.getElementById('question-box').innerHTML = `<strong>Q</strong> ${questions[currentQuestion].text}`;
        document.getElementById('explanation').style.display = 'none';
        document.getElementById('next-btn').style.display = 'none';
        document.querySelectorAll('.answer').forEach(el => el.classList.remove('unselected'));
    }
}
