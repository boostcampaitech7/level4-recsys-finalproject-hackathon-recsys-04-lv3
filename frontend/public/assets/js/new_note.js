function updateUploadBox(selection) {
  const uploadBox = document.getElementById("upload-box");
  const buttons = document.querySelectorAll(".button-select");
  buttons.forEach((btn) => btn.classList.remove("active"));
  document.getElementById(selection).classList.add("active");

  if (selection === "이미지" || selection === "문서") {
    const fileType = selection === "이미지" ? "이미지 파일" : "문서 파일";
    uploadBox.innerHTML = `
      <p>${fileType}을 업로드하세요.</p>
      <input type="file" class="input-box" accept="${selection === "이미지" ? "image/*" : ".pdf,.docx,.txt"}" />
  `;
  } else if (selection === "텍스트") {
    uploadBox.innerHTML = `
      <textarea class="input-box" placeholder="텍스트를 입력하세요."></textarea>
  `;
  }
}
async function analyzeNote() {
  const subject = document.querySelector("select.input-box").value; // 과목 선택
  const title = document.querySelector("input.input-box").value; // 제목 입력
  const uploadBox = document.getElementById("upload-box");
  const activeType = document.querySelector(".button-select.active").id; // 이미지, 문서, 텍스트 중 선택된 유형
  const formData = new FormData();
  const loadingOverlay = document.getElementById("loading-overlay"); // 로딩 화면 요소

  // 로딩 화면 표시
  loadingOverlay.classList.add("active");

  try {
    // 제목과 과목 필수 체크
    if (!subject || subject === "과목 선택") {
      alert("과목을 선택해주세요.");
      loadingOverlay.classList.remove("active"); // 로딩 화면 숨김
      return;
    }
    if (!title.trim()) {
      alert("제목을 입력해주세요.");
      loadingOverlay.classList.remove("active"); // 로딩 화면 숨김
      return;
    }

    formData.append("title", title);
    formData.append("subjects_id", subject);
    formData.append("user_id", localStorage.getItem("user_id"));

    // 업로드 데이터 처리
    if (activeType === "이미지" || activeType === "문서") {
      const fileInput = uploadBox.querySelector("input[type='file']");
      if (fileInput && fileInput.files.length > 0) {
        formData.append("file", fileInput.files[0]);
      } else {
        alert(`${activeType} 파일을 업로드해주세요.`);
        loadingOverlay.classList.remove("active"); // 로딩 화면 숨김
        return;
      }
    } else if (activeType === "텍스트") {
      const textArea = uploadBox.querySelector("textarea");
      if (textArea && textArea.value.trim()) {
        formData.append("content", textArea.value);
      } else {
        alert("텍스트를 입력해주세요.");
        loadingOverlay.classList.remove("active"); // 로딩 화면 숨김
        return;
      }
    }

    // API 호출
    const response = await fetch(
      activeType === "이미지" || activeType === "문서"
        ? "http://localhost:8000/api/v1/note/upload"
        : "http://localhost:8000/api/v1/note/text",
      {
        method: "POST",
        body: formData,
      }
    );

    if (response.ok) {
      const result = await response.json();
      alert("노트가 성공적으로 업로드되었습니다!");
      console.log(result);
      window.location.href = `new_note_analysis.html?note_id=${result.note_id}`;
    } else {
      const error = await response.json();
      alert(`업로드 실패: ${error.detail}`);
      console.log(error);
    }
  } catch (err) {
    console.error("업로드 중 오류 발생:", err);
    alert("업로드 중 오류가 발생했습니다.");
  } finally {
    // 로딩 화면 숨김
    loadingOverlay.classList.remove("active");
  }
}
