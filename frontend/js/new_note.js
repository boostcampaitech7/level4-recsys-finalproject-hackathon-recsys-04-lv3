function updateUploadBox(selection) {
  const uploadBox = document.getElementById('upload-box');
  const buttons = document.querySelectorAll('.button-select');
  buttons.forEach(btn => btn.classList.remove('active'));
  document.getElementById(selection).classList.add('active');
  
  if (selection === '이미지') {
      uploadBox.innerHTML = '노트 이미지를 드래그하여 넣어보세요.<br><button class="button-blue">이미지 불러오기</button>';
  } else if (selection === '문서') {
      uploadBox.innerHTML = '문서를 업로드하세요.<br><button class="button-blue">문서 불러오기</button>';
  } else if (selection === '텍스트') {
      uploadBox.innerHTML = '<textarea class="input-box" placeholder="텍스트를 입력하세요."></textarea>';
  }
}

function analyzeNote() {
  window.location.href = 'new_note_analysis.html';
}
