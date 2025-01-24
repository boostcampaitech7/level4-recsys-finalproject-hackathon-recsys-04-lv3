// new_note_analysis.js
const urlParams = new URLSearchParams(window.location.search);
const noteId = urlParams.get("note_id");
const userId = localStorage.getItem("user_id");
const SERVER_BASE_URL = 'http://127.0.0.1:8000';

async function fetchNoteData() {
   try {
       const [noteResponse, quizResponse] = await Promise.all([
           fetch(`${SERVER_BASE_URL}/api/v1/note/?note_id=${noteId}&user_id=${userId}`),
           fetch(`${SERVER_BASE_URL}/api/v1/quiz/next?user_id=${userId}&note_id=${noteId}`)
       ]);

       if (!noteResponse.ok || !quizResponse.ok) {
           throw new Error('API 요청 실패');
       }

       const noteData = await noteResponse.json();
       const quizData = await quizResponse.json();

       document.getElementById('note-title').textContent = noteData.title;
       document.getElementById('subject-name').textContent = `과목: ${noteData.subjects_id}`;
       document.querySelector('.feedback').textContent = noteData.feedback || '피드백이 없습니다';

       const imageContainer = document.querySelector('.image');
       imageContainer.innerHTML = '';

       if (noteData.is_analysis === 'Y') {
           const img = document.createElement('img');
           img.src = `${SERVER_BASE_URL}/api/v1/note/uploads?note_id=${noteId}&user_id=${userId}`;
           img.alt = '노트 이미지';
           img.style.maxWidth = '100%';
           imageContainer.appendChild(img);
       } else {
           const textElement = document.createElement('pre');
           textElement.textContent = noteData.raw_text;
           textElement.style.whiteSpace = 'pre-wrap';
           imageContainer.appendChild(textElement);
       }

       if (quizData.quiz) {
           const quizHtml = `
               <h3>OX 퀴즈</h3>
               <div class="quiz-item">
                   <p>${quizData.quiz.question}</p>
                   <div class="quiz-buttons">
                       <button onclick="solveQuiz('O', '${quizData.quiz.ox_id}')">O</button>
                       <button onclick="solveQuiz('X', '${quizData.quiz.ox_id}')">X</button>
                   </div>
               </div>
           `;
           document.querySelector('.recommendation').innerHTML = quizHtml;
       } else {
           document.querySelector('.recommendation').innerHTML = `
               <div class="quiz-item">
                   <p>모든 퀴즈를 푸셨습니다! 새로운 퀴즈를 불러오는 중...</p>
               </div>
           `;
           setTimeout(fetchNoteData, 1500);
       }
   } catch (error) {
       console.error('Error:', error);
       document.querySelector('.recommendation').innerHTML = `
           <div class="quiz-item">
               <p>퀴즈를 불러오는데 실패했습니다.</p>
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
       setTimeout(fetchNoteData, 2000);
   } catch (error) {
       console.error('Error:', error);
   }
}

function displayQuizResult(result) {
   const resultHtml = `
       <div class="quiz-result">
           <p>${result.result.is_correct}</p>
           <p>정답: ${result.result.correct_answer}</p>
           <p>해설: ${result.result.explanation}</p>
       </div>
   `;
   document.querySelector('.recommendation').innerHTML = resultHtml;
}

document.addEventListener('DOMContentLoaded', fetchNoteData);
