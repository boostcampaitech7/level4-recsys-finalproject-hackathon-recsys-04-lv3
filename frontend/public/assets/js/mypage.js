// mypage.js
document.addEventListener('DOMContentLoaded', async () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const userResponse = await fetch(`http://localhost:8000/api/v1/auth/user/${userId}`);
        const noteCountResponse = await fetch(`http://localhost:8000/api/v1/note/count/${userId}`);

        const userData = await userResponse.json();
        const noteCount = await noteCountResponse.json();

        renderUserProfile(userData);
        renderStats(noteCount);

    } catch (error) {
        console.error('Error:', error);
        showError('데이터를 불러오는데 실패했습니다.');
    }
 });

 function renderUserProfile(data) {
    const values = document.querySelectorAll('.profile-value');
    values[0].textContent = data.user_id;
    values[1].textContent = data.email;
    values[2].textContent = formatDate(data.signup_date);
 }

 function renderStats(noteCount) {
    const statsHtml = `
        <div class="stat-card">
            <h3>작성한 노트</h3>
            <p>${noteCount.count || 0}개</p>
        </div>
    `;
    document.getElementById('learningStats').innerHTML = statsHtml;
 }

 function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
 }

 function showError(message) {
    const mainContent = document.getElementById('main-content');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    mainContent.prepend(errorDiv);
 }
