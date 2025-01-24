const urlParams = new URLSearchParams(window.location.search);
const noteId = urlParams.get("note_id");
const userId = localStorage.getItem("user_id");
const SERVER_BASE_URL = 'http://127.0.0.1:8000';

console.log("전달된 noteId:", noteId);
console.log("전달된 userId:", userId);

async function fetchNoteData(noteId) {
  try {
    const response = await fetch(`${SERVER_BASE_URL}/api/v1/note/?note_id=${noteId}&user_id=${userId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    console.log(data);

    updateHTMLElements(data);
    loadImage(data.file_path);

  } catch (error) {
    console.error('노트 데이터를 가져오는 중 오류 발생:', error);
    document.getElementById('error-message').textContent = '노트를 불러오는 데 실패했습니다.';
  }
}

function updateHTMLElements(data) {
  document.getElementById('note-title').textContent = data.title;
  document.getElementById('subject-name').innerText = data.subjects_id;
  document.getElementById('note-feedback').textContent = data.feedback;
  // document.getElementById('note-text').textContent = data.cleaned_text;
}

function loadImage(imagePath) {
  const imageContainer = document.getElementById('note-image');
  imageContainer.innerHTML = '';

  console.log(`${SERVER_BASE_URL}${imagePath}`)

  if (imagePath) {
    const img = document.createElement('img');
    // img.src = `${SERVER_BASE_URL}/${imagePath}`;
    img.src = `${SERVER_BASE_URL}${imagePath}`;
    img.alt = '노트 이미지';
    img.style.maxWidth = '100%';
    imageContainer.appendChild(img);
  } else {
    imageContainer.textContent = '이미지가 없습니다.';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const subject = localStorage.getItem('selectedSubject') || '과목 없음';
  const title = localStorage.getItem('noteTitle') || '제목 없음';

  document.getElementById('subject-name').innerText = subject;
  document.getElementById('note-title').innerText = title;

  const today = new Date().toISOString().split('T')[0];
  document.getElementById('note-date').innerText = today;

  fetchNoteData(noteId);
});
