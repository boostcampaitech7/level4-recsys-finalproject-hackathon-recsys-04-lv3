document.addEventListener("DOMContentLoaded", function () {
  const userId = localStorage.getItem("user_id")
  const apiUrl = `http://localhost:8000/api/v1/note/list?user_id=${userId}`;

  // fetch로 백엔드에서 데이터 가져오기
  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      const notes = data.notes;

      if (notes && notes.length > 0) {
        const noteList = document.getElementById('note-list');
        notes.forEach(note => {
          const noteItem = document.createElement('li');
          noteItem.classList.add('note-item');

          // Note Date Formatting
          let dateStr = note.note_date;
          let date = new Date(dateStr);
          let year = date.getFullYear();
          let month = String(date.getMonth() + 1).padStart(2, '0');
          let day = String(date.getDate()).padStart(2, '0');
          let formattedDate = `${year}-${month}-${day}`;

          // Note Link
          let link = "./note_detail.html"

          noteItem.innerHTML = `<a href="${link}">${note.title}</a><span>${formattedDate}</span>`;
          noteList.appendChild(noteItem);
        });
      } else {
        noteListContainer.innerHTML = "<li>작성한 노트가 없습니다.</li>";
      }
    })
    .catch(error => {
      console.error("노트 데이터를 불러오는 중 오류가 발생했습니다.", error);
    });
});

// 날짜 형식 변환 함수 (YYYY년 MM월 DD일 형식)
function formatDate(dateStr) {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}년 ${month}월 ${day}일`;
}

// 분석 버튼 클릭 시 분석 시작 함수 (기능 구현 필요)
function startAnalysis(noteId) {
  console.log(`Note ${noteId} 분석 시작!`);
  // 분석 기능을 추가해야 할 부분
}
