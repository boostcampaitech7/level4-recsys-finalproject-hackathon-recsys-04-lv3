document.addEventListener("DOMContentLoaded", function () {
    const userId = localStorage.getItem("user_id");
    const subjectFilter = document.getElementById('subjectFilter');
    const sortToggleBtn = document.getElementById('sortToggle');
    let isNewest = true;
    let isLoading = false;

    // 초기 로드
    initialize();

    async function initialize() {
        await Promise.all([loadSubjects(), loadNotes()]);
        setupEventListeners();
    }

    function setupEventListeners() {
        subjectFilter.addEventListener('change', handleFilterChange);
        sortToggleBtn.addEventListener('click', handleSortToggle);
    }

    async function handleFilterChange() {
        if (!isLoading) {
            showLoadingState();
            await loadNotes();
            hideLoadingState();
        }
    }

    function handleSortToggle() {
        if (!isLoading) {
            isNewest = !isNewest;
            sortToggleBtn.textContent = isNewest ? '최신순' : '오래된순';
            sortToggleBtn.classList.toggle('asc', !isNewest);
            loadNotes();
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

    async function loadNotes() {
        if (isLoading) return;

        try {
            isLoading = true;
            showLoadingState();

            const subject = subjectFilter.value;
            const url = `http://localhost:8000/api/v1/note/list?user_id=${userId}&sort=${isNewest ? 'newest' : 'oldest'}${subject ? `&subject=${subject}` : ''}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load notes');

            const data = await response.json();
            renderNotes(data.notes);
        } catch (error) {
            console.error("Error loading notes:", error);
            showError("노트를 불러오는데 실패했습니다.");
        } finally {
            isLoading = false;
            hideLoadingState();
        }
    }

    function renderNotes(notes) {
        const noteList = document.getElementById('note-list');

        if (!notes?.length) {
            noteList.innerHTML = `
                <li class="note-item empty-state">
                    <div class="empty-message">
                        <p>작성한 노트가 없습니다.</p>
                        <a href="new_note.html" class="create-note-btn">새 노트 작성하기</a>
                    </div>
                </li>
            `;
            return;
        }

        noteList.innerHTML = notes.map(note => `
            <li class="note-item">
                <a href="new_note_analysis.html?note_id=${note.note_id}" class="note-link">
                    <span class="note-title">${escapeHtml(note.title)}</span>
                    <span class="note-date">${formatDate(note.note_date)}</span>
                </a>
            </li>
        `).join('');
    }

    function showLoadingState() {
        const noteList = document.getElementById('note-list');
        noteList.innerHTML = `
            <li class="note-item loading">
                <div class="loading-spinner"></div>
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
        const noteList = document.getElementById('note-list');
        noteList.innerHTML = `
            <li class="note-item error">
                <div class="error-message">${message}</div>
            </li>
        `;
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        date.setHours(date.getHours() + 9);
        return `${date.getFullYear()}년 ${String(date.getMonth() + 1).padStart(2, '0')}월 ${String(date.getDate()).padStart(2, '0')}일`;
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
