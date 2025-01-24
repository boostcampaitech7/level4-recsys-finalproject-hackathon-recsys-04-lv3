// mypage.js
document.addEventListener('DOMContentLoaded', async () => {
    const userId = localStorage.getItem("user_id");
    const token = localStorage.getItem("token");

    if (!userId || !token) {
        window.location.href = "login.html";
        return;
    }

    try {
        const [userData, notesCount] = await Promise.all([
            fetch(`http://127.0.0.1:8000/api/v1/auth/user/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(res => res.json()),
            fetch(`http://127.0.0.1:8000/api/v1/note/count/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(res => res.json())
        ]);

        renderUserProfile(userData);
        renderLearningStats(userData, notesCount.count);
        await loadRecentActivities(userId);
        renderPerformanceMetrics(userData);

    } catch (error) {
        console.error(error);
        showError("데이터를 불러오는 중 오류가 발생했습니다.");
    }
});

function formatDate(dateStr) {
    const date = new Date(dateStr);
    date.setHours(date.getHours() + 9);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    date.setHours(date.getHours() + 9);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
        return `오늘 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
    } else if (date.toDateString() === yesterday.toDateString()) {
        return `어제 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
    }
    return `${date.getMonth() + 1}월 ${date.getDate()}일 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function renderUserProfile(data) {
    const profileValues = document.querySelectorAll('.profile-value');
    profileValues[0].textContent = data.user_id;
    profileValues[1].textContent = data.email;
    profileValues[2].textContent = formatDate(data.signup_date);
}

function renderLearningStats(userData, notesCount) {
    const statsHtml = `
        <div class="stat-card">
            <h3>총 학습 시간</h3>
            <p>${userData.total_study_hours || 0}시간</p>
        </div>
        <div class="stat-card">
            <h3>학습 노트</h3>
            <p>${notesCount || 0}개</p>
        </div>
        <div class="stat-card">
            <h3>퀴즈 성과</h3>
            <p>정답률: ${userData.quiz_accuracy || 0}%</p>
        </div>
    `;
    document.getElementById('learningStats').innerHTML = statsHtml;
}

async function loadRecentActivities(userId) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/note/list/${userId}`);
        if (!response.ok) {
            throw new Error('노트 목록을 불러오는데 실패했습니다');
        }
        const { notes } = await response.json();

        const activitiesHtml = notes.map(note => `
            <div class="activity-item">
                <span class="activity-date">${formatDateTime(note.note_date)}</span>
                <span class="activity-type">노트 작성</span>
                <span class="activity-detail">${note.title}</span>
            </div>
        `).join('');

        document.getElementById('recentActivities').innerHTML = activitiesHtml || '<p>최근 활동이 없습니다.</p>';
    } catch (error) {
        console.error('활동 기록 로드 실패:', error);
        document.getElementById('recentActivities').innerHTML = '<p>데이터를 불러오는데 실패했습니다.</p>';
    }
}

function renderPerformanceMetrics(data) {
    const metricsHtml = `
        <div class="metric-card">
            <h3>주간 학습 목표 달성률</h3>
            <p>${data.weekly_goal_progress || 0}%</p>
        </div>
        <div class="metric-card">
            <h3>연속 학습일</h3>
            <p>${data.streak_days || 0}일</p>
        </div>
        <div class="metric-card">
            <h3>월간 퀴즈 정답률 추이</h3>
            <p>${data.monthly_quiz_trend || '데이터 없음'}</p>
        </div>
    `;
    document.getElementById('performanceMetrics').innerHTML = metricsHtml;
}

function getActivityType(type) {
    const types = {
        note_create: '새 노트 작성',
        note_update: '노트 수정',
        quiz_complete: '퀴즈 완료',
        feedback_received: '피드백 수신'
    };
    return types[type] || type;
}

function getDefaultDescription(activity) {
    switch (activity.type) {
        case 'note_create':
            return '새로운 학습 노트를 작성했습니다';
        case 'note_update':
            return '학습 노트를 수정했습니다';
        case 'quiz_complete':
            return '퀴즈를 완료했습니다';
        case 'feedback_received':
            return '피드백을 받았습니다';
        default:
            return '활동을 기록했습니다';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    document.querySelector('main').prepend(errorDiv);
}
