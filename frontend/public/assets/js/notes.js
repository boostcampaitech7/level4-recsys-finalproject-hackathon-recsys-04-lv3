// notes.js
document.addEventListener("DOMContentLoaded", function () {
  const userId = localStorage.getItem("user_id");
  const subjectFilter = document.getElementById('subjectFilter');
  const sortToggleBtn = document.getElementById('sortToggle');
  let isNewest = true;

  loadSubjects();
  loadNotes();

  subjectFilter.addEventListener('change', loadNotes);
  sortToggleBtn.addEventListener('click', () => {
      isNewest = !isNewest;
      sortToggleBtn.textContent = isNewest ? '최신순' : '오래된순';
      loadNotes();
  });

  async function loadSubjects() {
      try {
          const response = await fetch(`http://localhost:8000/api/v1/note/subjects?user_id=${userId}`);
          const data = await response.json();

          subjectFilter.innerHTML = '<option value="">전체 과목</option>' +
              data.subjects.map(subject =>
                  `<option value="${subject}">${subject}</option>`
              ).join('');
      } catch (error) {
          console.error("Error loading subjects:", error);
      }
  }

  async function loadNotes() {
      try {
          const subject = subjectFilter.value;
          const url = `http://localhost:8000/api/v1/note/list?user_id=${userId}&sort=${isNewest ? 'newest' : 'oldest'}${subject ? `&subject=${subject}` : ''}`;
          const response = await fetch(url);
          const data = await response.json();

          const noteList = document.getElementById('note-list');
          noteList.innerHTML = data.notes?.length > 0 ?
              data.notes.map(note => `
                  <li class="note-item">
                      <a href="new_note_analysis.html?note_id=${note.note_id}" class="note-link">
                          ${note.title}
                          <span class="note-date">${formatDate(note.note_date)}</span>
                      </a>
                  </li>
              `).join('') :
              "<li>작성한 노트가 없습니다.</li>";
      } catch (error) {
          console.error("Error:", error);
          document.getElementById('note-list').innerHTML = "<li>노트를 불러오는데 실패했습니다.</li>";
      }
  }
});

function formatDate(dateStr) {
  const date = new Date(dateStr);
  date.setHours(date.getHours() + 9);
  return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;
}
