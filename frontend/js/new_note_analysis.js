document.addEventListener('DOMContentLoaded', function () {
  // 저장된 데이터 가져오기
  const subject = localStorage.getItem('selectedSubject') || '과목 없음';
  const title = localStorage.getItem('noteTitle') || '제목 없음';

  // 페이지에 데이터 적용
  document.getElementById('subject-name').innerText = subject;
  document.getElementById('note-title').innerText = title;

  // 오늘 날짜 적용
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('note-date').innerText = today;
});
