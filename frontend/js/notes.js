document.addEventListener('DOMContentLoaded', function() {
  const notes = [
      { title: "메모 제목 1", date: "2025-01-20", link: "note_detail.html" },
      { title: "메모 제목 2", date: "2025-01-19", link: "note_detail.html" },
      { title: "메모 제목 3", date: "2025-01-18", link: "note_detail.html" }
  ];
  
  const noteList = document.getElementById('note-list');
  notes.forEach(note => {
      const noteItem = document.createElement('li');
      noteItem.classList.add('note-item');
      noteItem.innerHTML = `<a href="${note.link}">${note.title}</a><span>${note.date}</span>`;
      noteList.appendChild(noteItem);
  });
});
