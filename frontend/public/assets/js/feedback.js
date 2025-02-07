document.addEventListener("DOMContentLoaded", function () {
    const userId = localStorage.getItem("user_id");
    const subjectFilter = document.getElementById('subjectFilter');
    const sortToggleBtn = document.getElementById('sortToggle');
    let isNewest = true;
    let isLoading = false;

    initialize();

    async function initialize() {
        if (!userId) {
            window.location.href = 'index.html';
            return;
        }
        await Promise.all([loadSubjects(), loadFeedback()]);
        setupEventListeners();
    }

    function setupEventListeners() {
        subjectFilter.addEventListener('change', handleFilterChange);
        sortToggleBtn.addEventListener('click', handleSortToggle);
    }

    async function handleFilterChange() {
        if (!isLoading) {
            await loadFeedback();
        }
    }

    function handleSortToggle() {
        if (!isLoading) {
            isNewest = !isNewest;
            sortToggleBtn.textContent = isNewest ? '최신순' : '오래된순';
            sortToggleBtn.classList.toggle('asc', !isNewest);
            loadFeedback();
        }
    }

    async function loadSubjects() {
        try {
            const response = await fetch(`http://localhost:8000/api/v1/note/subjects?user_id=${userId}`);
            if (!response.ok) throw new Error('Failed to load subjects');

            const data = await response.json();
            renderSubjects(data.subjects || []);
        } catch (error) {
            console.error("Error loading subjects:", error);
            showError("과목 목록을 불러오는데 실패했습니다.");
        }
    }

    function renderSubjects(subjects) {
        subjectFilter.innerHTML = `
            <option value="">전체 과목</option>
            ${subjects.map(subject =>
            `<option value="${subject}">${escapeHtml(subject)}</option>`
        ).join('')}
        `;
    }

    async function loadFeedback() {
        if (isLoading) return;

        try {
            isLoading = true;
            showLoadingState();

            const subject = subjectFilter.value;
            // subjects_id로 필터링하도록 수정
            const url = `http://localhost:8000/api/v1/user/${userId}/feedbacks?fields=note_title,feedback,created_at,subject,note_subject&sort=${isNewest ? 'newest' : 'oldest'}${subject ? `&subjects_id=${subject}` : ''}`;

            console.log('요청 URL:', url);

            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load feedbacks');

            const data = await response.json();
            console.log('서버 응답 데이터:', data);

            // 데이터 필터링 로직 추가
            const filteredFeedbacks = subject ?
                data.feedbacks.filter(feedback =>
                    feedback.subject === subject ||
                    feedback.note_subject === subject ||
                    feedback.subjects_id === subject
                ) : data.feedbacks;

            renderFeedbacks(filteredFeedbacks || []);
        } catch (error) {
            console.error("Error loading feedbacks:", error);
            showError("피드백을 불러오는데 실패했습니다.");
        } finally {
            isLoading = false;
            hideLoadingState();
        }
    }

    function renderStructuredFeedback(feedbackXml) {
        // XML 파서 생성
        const parser = new DOMParser();
        const escapeXml = feedbackXml.replace(/&/g, "&amp;")
        // .replace(/</g, "&lt;")
        // .replace(/>/g, "&gt;")
        // .replace(/"/g, "&quot;")
        // .replace(/'/g, "&#039;");
        const xmlDoc = parser.parseFromString(escapeXml, "text/xml");

        // 결과를 저장할 HTML 문자열
        let feedbackHtml = '';

        // 성공 케이스 확인
        const successCase = xmlDoc.querySelector('feedback-case[type="success"]');
        if (successCase) {
            feedbackHtml = `
            <div class="feedback-success">
                <div class="success-icon">✓</div>
                 <p class="success-message">${successCase.querySelector('correct').textContent}</p>
            </div>
        `;
        } else {
            // 에러 케이스 처리
            const errorCases = xmlDoc.querySelectorAll('feedback-case[type="error"] item');
            feedbackHtml = `
            <div class="feedback-errors">
                ${Array.from(errorCases).map(item => `
                    <div class="error-item">
                        <div class="error-number">${item.querySelector('number').textContent}</div>
                        <div class="error-content">
                            <div class="wrong-text">
                                <p class="text"><span class="label">잘못된 부분:</span> ${item.querySelector('wrong').textContent}</p>
                            </div>
                            <div class="correct-text">
                                <p class="text"><span class="label">수정 사항:</span> ${item.querySelector('correct').textContent}</p>
                            </div>
                            <div class="explanation-text">
                                <p class="text">💡 ${item.querySelector('explanation').textContent}</p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        }

        return feedbackHtml;
    }

    function renderFeedbacks(feedbacks) {
        const feedbackList = document.querySelector('.feedback-list');
        const currentSubject = subjectFilter.value;

        if (!feedbacks || feedbacks.length === 0) {
            feedbackList.innerHTML = `
                <li class="feedback-item empty-state">
                    <p>${currentSubject ? `'${currentSubject}' 과목의 피드백이 없습니다.` : '피드백이 없습니다.'}</p>
                </li>
            `;
            return;
        }

        feedbackList.innerHTML = feedbacks
            .map(feedback => {
                const title = escapeHtml(feedback.note_title || '제목 없음');
                const content = feedback.feedback || '';
                const date = formatDate(feedback.created_at);
                const subject = escapeHtml(
                    feedback.subject ||
                    feedback.note_subject ||
                    (feedback.subjects_id === "과목 없음" ? "전체" : feedback.subjects_id) ||
                    '전체'
                );

                let renderedContent;
                try {
                    renderedContent = content.trim().startsWith('<feedback-case') ?
                        renderStructuredFeedback(content) :
                        `<div class="feedback-content">${escapeHtml(content)}</div>`;
                } catch (error) {
                    console.error('피드백 렌더링 에러:', error);
                    renderedContent = `<div class="feedback-content">${escapeHtml(content)}</div>`;
                }

                return `
                    <li class="feedback-item">
                        <div class="feedback-header">
                            <div class="feedback-info">
                                <div class="feedback-title-row">
                                    <strong class="note-title">${title}</strong>
                                    <span class="feedback-subject">${subject}</span>
                                </div>
                                <span class="feedback-date">${date}</span>
                            </div>
                        </div>
                        ${renderedContent}
                    </li>
                `;
            })
            .join('');
    }

    function showLoadingState() {
        const feedbackList = document.querySelector('.feedback-list');
        feedbackList.innerHTML = `
            <li class="feedback-item loading">
                <div class="loading-spinner"></div>
                <p>피드백을 불러오는 중...</p>
            </li>
        `;
    }

    function hideLoadingState() {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    function showError(message) {
        const feedbackList = document.querySelector('.feedback-list');
        feedbackList.innerHTML = `
            <li class="feedback-item error">
                <div class="error-message">${message}</div>
                <button onclick="loadFeedback()" class="retry-btn">다시 시도</button>
            </li>
        `;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
