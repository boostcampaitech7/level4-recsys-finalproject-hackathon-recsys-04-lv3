document.addEventListener('DOMContentLoaded', function () {
  const state = {
    currentType: '업로드',
    isUploading: false
  };

  function initialize() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      window.location.href = 'index.html';
      return;
    }

    setupEventListeners();
    updateUploadBox('업로드');
    setupDragAndDrop();

    document.querySelector('.logout-btn').addEventListener('click', () => {
      localStorage.clear();
      window.location.href = 'index.html';
    });
  }

  function setupEventListeners() {
    document.querySelectorAll('.button-select').forEach(button => {
      button.addEventListener('click', () => updateUploadBox(button.id));
    });

    document.getElementById('analyzeBtn').addEventListener('click', analyzeNote);
  }

  function setupDragAndDrop() {
    const uploadBox = document.getElementById('upload-box');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      uploadBox.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
      uploadBox.addEventListener(eventName, () => {
        uploadBox.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      uploadBox.addEventListener(eventName, () => {
        uploadBox.classList.remove('drag-over');
      });
    });

    uploadBox.addEventListener('drop', handleDrop);
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    const fileInput = document.querySelector('input[type="file"]');

    if (fileInput && files.length > 0) {
      fileInput.files = files;
      handleFileSelect({ target: fileInput });
    }
  }

  async function handleFileSelect(event) {
    const file = event.target?.files?.[0];
    if (!file) return;

    const uploadBox = document.getElementById('upload-box');

    // 기존 미리보기 및 안내 문구 제거
    clearExistingPreviews(uploadBox);

    // 파일 타입 표시기 생성
    const typeIndicator = createTypeIndicator();

    // 숨겨진 파일 입력 필드 생성 및 추가 (기존 파일 유지)
    const hiddenFileInput = document.createElement('input');
    hiddenFileInput.type = 'file';
    hiddenFileInput.className = 'input-box';
    hiddenFileInput.accept = 'image/*,.pdf';
    hiddenFileInput.style.display = 'none';
    hiddenFileInput.files = event.target.files; // 기존 파일 복사
    hiddenFileInput.addEventListener('change', handleFileSelect);
    uploadBox.appendChild(hiddenFileInput);

    try {
      if (file.type.startsWith('image/')) {
        await handleImagePreview(file, uploadBox, typeIndicator);
      } else if (file.type === 'application/pdf') {
        await handlePDFPreview(file, uploadBox, typeIndicator);
      } else {
        throw new Error('지원하지 않는 파일 형식입니다. 이미지 또는 PDF 파일만 업로드 가능합니다.');
      }
    } catch (error) {
      handlePreviewError(error, event, uploadBox);
    }
  }

  function clearExistingPreviews(uploadBox) {
    // 기존 미리보기 및 안내 문구만 제거
    const preview = uploadBox.querySelector('.upload-preview');
    const indicator = uploadBox.querySelector('.file-type-indicator');
    const text = uploadBox.querySelectorAll('p');

    if (preview) preview.remove();
    if (indicator) indicator.remove();
    text.forEach(p => p.remove());
  }


  function createTypeIndicator() {
    const typeIndicator = document.createElement('div');
    typeIndicator.className = 'file-type-indicator';

    // 3초 후에 fade-out 클래스 추가
    setTimeout(() => {
      typeIndicator.classList.add('fade-out');

      // fade-out 애니메이션이 끝나면 요소 제거
      typeIndicator.addEventListener('animationend', () => {
        typeIndicator.remove();
      });
    }, 1500);

    return typeIndicator;
  }

  function handleImagePreview(file, uploadBox, typeIndicator) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = function (e) {
        try {
          const preview = document.createElement('img');
          preview.src = e.target.result;
          preview.className = 'upload-preview';
          preview.style.maxWidth = '100%';
          preview.style.height = 'auto';
          preview.style.borderRadius = '8px';
          preview.style.marginBottom = '10px';

          // 이미지 로드 완료 후 업로드 박스에 추가
          preview.onload = function () {
            uploadBox.appendChild(preview);
            typeIndicator.textContent = '이미지 파일';
            uploadBox.appendChild(typeIndicator);
            resolve();
          };

          preview.onerror = function () {
            reject(new Error('이미지 로드 실패'));
          };
        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error('파일 읽기 실패'));
      reader.readAsDataURL(file);
    });
  }

  function handlePDFPreview(file, uploadBox, typeIndicator) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = function (e) {
        try {
          // PDF blob URL 생성
          const blob = new Blob([e.target.result], { type: 'application/pdf' });
          const blobUrl = URL.createObjectURL(blob);

          // iframe 생성
          const iframe = document.createElement('iframe');
          iframe.className = 'upload-preview';
          iframe.src = blobUrl;
          iframe.style.width = '100%';
          iframe.style.height = '500px'; // 높이 조정 가능
          iframe.style.border = '1px solid #ddd';
          iframe.style.borderRadius = '8px';
          iframe.style.marginBottom = '10px';

          // iframe 로드 완료 이벤트
          iframe.onload = function () {
            typeIndicator.textContent = 'PDF 문서';
            resolve();
          };

          // iframe 로드 실패 이벤트
          iframe.onerror = function () {
            reject(new Error('PDF 미리보기 로드 실패'));
          };

          // 업로드 박스에 추가
          uploadBox.appendChild(iframe);
          uploadBox.appendChild(typeIndicator);

          // Blob URL 정리를 위한 이벤트 리스너 추가
          iframe.addEventListener('load', () => {
            URL.revokeObjectURL(blobUrl);
          });
        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error('파일 읽기 실패'));
      reader.readAsArrayBuffer(file);
    });
  }

  function handlePreviewError(error, event, uploadBox) {
    console.error('미리보기 생성 실패:', error);

    // 입력 필드 초기화
    if (event.target) {
      event.target.value = '';
    }

    // 에러 메시지 표시
    const errorMsg = document.createElement('p');
    errorMsg.textContent = error.message || '파일 미리보기를 불러올 수 없습니다.';
    errorMsg.className = 'upload-preview error-message';
    errorMsg.style.color = '#ff4444';
    errorMsg.style.textAlign = 'center';
    errorMsg.style.marginTop = '10px';

    clearExistingPreviews(uploadBox);
    uploadBox.appendChild(errorMsg);
  }

  function updateUploadBox(selection) {
      state.currentType = selection;
      const uploadBox = document.getElementById('upload-box');
      const buttons = document.querySelectorAll('.button-select');

      buttons.forEach(btn => btn.classList.remove('active'));
      document.getElementById(selection).classList.add('active');

      if (selection === '업로드') {
          uploadBox.innerHTML = `
              <p class="upload-desc">이미지 또는 PDF 파일을 드래그하여 놓거나 클릭하여 선택하세요</p>
              <div class="file-input-container">
                  <input type="file" class="input-box" accept="image/*,.pdf" id="file-input" />
                  <label for="file-input" class="file-input-label">파일 선택</label>
              </div>
          `;

          const fileInput = uploadBox.querySelector('input[type="file"]');
          if (fileInput) {
              fileInput.addEventListener('change', handleFileSelect);
          }
      } else if (selection === '텍스트') {
          uploadBox.innerHTML = `
              <textarea class="input-box custom-textarea" placeholder="텍스트를 입력하세요."></textarea>
          `;
      }
  }

  async function analyzeNote() {
    if (state.isUploading) return;

    const subject = document.getElementById('subjectSelect').value;
    const title = document.getElementById('titleInput').value;
    const loadingOverlay = document.getElementById('loading-overlay');

    if (!validateInputs(subject, title)) return;
    try {
      state.isUploading = true;
      loadingOverlay.classList.add('active');

      const formData = createFormData(subject, title);
      if (!formData) {
        loadingOverlay.classList.remove('active');
        return;
      }

      const response = await sendRequest(formData);
      await handleResponse(response);

    } catch (error) {
      handleError(error);
    } finally {
      state.isUploading = false;
      loadingOverlay.classList.remove('active');
    }
  }

  function validateInputs(subject, title) {
    if (!title.trim()) {
      alert('제목을 입력해주세요.');
      return false;
    }
    return true;
  }

  function createFormData(subject, title) {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('subjects_id', subject);
    formData.append('user_id', localStorage.getItem('user_id'));

    const uploadBox = document.getElementById('upload-box');

    if (state.currentType === '업로드') {
      const fileInput = uploadBox.querySelector('input[type="file"]');
      if (!fileInput?.files?.length) {
        alert('파일을 업로드해주세요.');
        return null;
      }
      formData.append('file', fileInput.files[0]);
    } else if (state.currentType === '텍스트') {
      const textArea = uploadBox.querySelector('textarea');
      if (!textArea?.value?.trim()) {
        alert('텍스트를 입력해주세요.');
        return null;
      }
      formData.append('content', textArea.value);
    }

    return formData;
  }

  async function sendRequest(formData) {
    const endpoint = state.currentType === '텍스트'
      ? 'http://localhost:8000/api/v1/note/text'
      : 'http://localhost:8000/api/v1/note/upload';

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData
    });

    return response;
  }

  async function handleResponse(response) {
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '업로드에 실패했습니다.');
    }

    const result = await response.json();
    alert('노트가 성공적으로 업로드되었습니다!');
    window.location.href = `new_note_analysis.html?note_id=${result.note_id}`;
  }

  function handleError(error) {
    console.error('업로드 중 오류 발생:', error);
    alert(`업로드 중 오류가 발생했습니다: ${error.message}`);
  }

  initialize();
});
