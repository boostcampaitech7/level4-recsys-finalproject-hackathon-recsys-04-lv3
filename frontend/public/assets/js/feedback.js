// 피드백 파싱 및 렌더링 함수
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

document.addEventListener('DOMContentLoaded', () => {
    const userId = localStorage.getItem('user_id');
    const subjectFilter = document.getElementById('subjectFilter');
    const sortToggleBtn = document.getElementById('sortToggle');
    let isNewest = true;
    let isLoading = false;

    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    initialize();

    async function initialize() {
        await Promise.all([loadSubjects(), loadFeedback()]);
        setupEventListeners();
    }

    function setupEventListeners() {
        subjectFilter.addEventListener('change', handleFilterChange);
        sortToggleBtn.addEventListener('click', handleSortToggle);
    }

    async function handleFilterChange() {
        if (!isLoading) {
            isLoading = true;
            showLoadingState();
            try {
                await loadFeedback();
            } finally {
                isLoading = false;
                hideLoadingState();
            }
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
            renderSubjects(data.subjects);
        } catch (error) {
            console.error("Error loading subjects:", error);
            showError("과목 목록을 불러오는데 실패했습니다.");
        }
    }

    function renderSubjects(subjects) {
        subjectFilter.innerHTML = `
            <option value="">전체 과목</option>
            ${subjects.map(subject =>
            `<option value="${subject}">${subject}</option>`
        ).join('')}
        `;
    }

    async function loadFeedback() {
        if (isLoading) return;

        try {
            isLoading = true;
            showLoadingState();

            const subject = subjectFilter.value;
            const url = `http://localhost:8000/api/v1/user/${userId}/feedbacks?fields=note_title,feedback,created_at,subject,note_subject&sort=${isNewest ? 'newest' : 'oldest'}${subject ? `&subject=${encodeURIComponent(subject)}` : ''}`;

            console.log('정렬 상태:', isNewest ? 'newest' : 'oldest'); // 정렬 상태 확인
            console.log('요청 URL:', url);

            const response = await fetch(url);
            const data = await response.json();

            console.log('서버 응답 데이터:', data); // 응답 데이터 확인

            if (!data.feedbacks || data.feedbacks.length === 0) {
                const feedbackList = document.querySelector('.feedback-list');
                feedbackList.innerHTML = `
                    <li class="feedback-item empty-state">
                        <p>${subject ? `'${subject}' 과목의 피드백이 없습니다.` : '피드백이 없습니다.'}</p>
                    </li>
                `;
                return;
            }

            renderFeedbacks(data.feedbacks);
        } catch (error) {
            console.error('Error loading feedbacks:', error);
            showError('피드백을 불러오는데 실패했습니다.');
        } finally {
            isLoading = false;
            hideLoadingState();
        }
    }

    function renderFeedbacks(feedbacks) {
        const feedbackList = document.querySelector('.feedback-list');

        if (!feedbacks || feedbacks.length === 0) {
            feedbackList.innerHTML = `
                <li class="feedback-item empty-state">
                    <p>피드백이 없습니다.</p>
                </li>
            `;
            return;
        }

        console.log('Feedback data to render:', feedbacks); // 데이터 확인용 로그

        feedbackList.innerHTML = feedbacks
            .map(feedback => {
                // 데이터 구조 로깅
                console.log('Processing feedback:', {
                    title: feedback.note_title,
                    subject: feedback.subject,
                    noteSubject: feedback.note_subject,
                    subjectsId: feedback.subjects_id
                });

                const title = escapeHtml(feedback.note_title || '제목 없음');
                const content = feedback.feedback;
                const date = formatDate(feedback.created_at);

                // 과목명 우선순위: subject -> note_subject -> subjects_id
                const subject = escapeHtml(
                    feedback.subject ||
                    feedback.note_subject ||
                    (feedback.subjects_id === "과목 없음" ? "전체" : feedback.subjects_id) ||
                    '전체'
                );
                try {
                    const renderedFeedback = content.startsWith('<feedback-case')
                        ? renderStructuredFeedback(content)
                        : escapeHtml(content);

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
                        ${renderedFeedback}
                    </li>
                `;
                }
                catch (error) {
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
                        <pre class="feedback-content">${escapeHtml(content)}</pre>
                    </li>
                `;
                }



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

    function showError(message) {
        const mainContent = document.getElementById('main-content');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <p>${message}</p>
            <button onclick="loadFeedback()" class="retry-btn">
                다시 시도
            </button>
        `;
        mainContent.prepend(errorDiv);
    }
});
