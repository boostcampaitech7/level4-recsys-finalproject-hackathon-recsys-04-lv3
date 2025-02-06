document.addEventListener('DOMContentLoaded', async () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    showLoadingState();

    try {
        const [userResponse, noteCountResponse, recentActivitiesResponse] = await Promise.all([
            fetch(`http://localhost:8000/api/v1/auth/user/${userId}`),
            fetch(`http://localhost:8000/api/v1/note/count/${userId}`),
            fetch(`http://localhost:8000/api/v1/activities/${userId}`)
        ]);

        const userData = await userResponse.json();
        const noteCount = await noteCountResponse.json();
        const recentActivities = await recentActivitiesResponse.json();

        renderUserProfile(userData);
        renderStats(noteCount);
        renderRecentActivities(recentActivities);

        hideLoadingState();
    } catch (error) {
        console.error('Error:', error);
        showError('데이터를 불러오는데 실패했습니다.');
        hideLoadingState();
    }
});

function showLoadingState() {
    const mainContent = document.getElementById('main-content');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-spinner';
    loadingDiv.innerHTML = `
        <div class="spinner"></div>
        <p>데이터를 불러오는 중입니다...</p>
    `;
    mainContent.prepend(loadingDiv);
}

function hideLoadingState() {
    const loadingSpinner = document.querySelector('.loading-spinner');
    if (loadingSpinner) {
        loadingSpinner.remove();
    }
}

function renderUserProfile(data) {
    const values = document.querySelectorAll('.profile-value');
    values[0].textContent = data.user_id;
    values[1].textContent = data.email;
    values[2].textContent = formatDate(data.signup_date);

    // Add animation
    values.forEach((value, index) => {
        setTimeout(() => {
            value.style.opacity = '1';
            value.style.transform = 'translateX(0)';
        }, index * 200);
    });
}

function renderStats(noteCount) {
    const stats = [
        { title: "완료한 퀴즈", value: noteCount.quiz_count || 0, unit: "개" },
        { title: "학습 시간", value: noteCount.study_time || 0, unit: "시간" }
    ];

    const statsHtml = stats.map(stat => `
        <div class="stat-card">
            <h3>${stat.title}</h3>
            <p>${stat.value}${stat.unit}</p>
        </div>
    `).join('');

    const statsContainer = document.getElementById('learningStats');
    statsContainer.innerHTML = `
        <div class="stat-card pie-chart-container">
            <h3>작성한 노트</h3>
            <canvas id="notePieChart"></canvas>
        </div>
        ${statsHtml}
    `;

    // Add animation
    const cards = statsContainer.querySelectorAll('.stat-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // 📌 파이 차트 데이터 준비
    const MAX_ITEMS = 5;
    const COLORS = ["#A2CFFF", "#A8E6CF", "#FFF3B0", "#FFB3A7", "#D4A6FF"];

    const pieChartData = (noteCount.counts || [])
        .sort((a, b) => b.count - a.count)
        .slice(0, MAX_ITEMS)
        .map((item, index) => ({
            label: item.subjects_id,
            value: item.count,
            color: COLORS[index % COLORS.length]
        }));

    const ctx = document.getElementById("notePieChart").getContext("2d");
    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: pieChartData.map(item => item.label),
            datasets: [{
                data: pieChartData.map(item => item.value),
                backgroundColor: pieChartData.map(item => item.color)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: function(tooltipItem) {
                            return tooltipItem.label + ': ' + tooltipItem.raw;
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}


function renderRecentActivities(activities) {
    if (!activities || !activities.length) {
        document.getElementById('recentActivities').innerHTML = '<p class="no-activities">최근 활동이 없습니다.</p>';
        return;
    }

    const activitiesHtml = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">${getActivityIcon(activity.type)}</div>
            <div class="activity-content">
                <p class="activity-text">${activity.description}</p>
                <p class="activity-date">${formatDate(activity.date)}</p>
            </div>
        </div>
    `).join('');

    document.getElementById('recentActivities').innerHTML = activitiesHtml;
}

function getActivityIcon(type) {
    const icons = {
        note: '📝',
        quiz: '✍️',
        feedback: '💭',
        login: '🔑'
    };
    return icons[type] || '📌';
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleString('ko-KR', options);
}

function showError(message) {
    const mainContent = document.getElementById('main-content');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;

    // Add animation
    errorDiv.style.opacity = '0';
    errorDiv.style.transform = 'translateY(-20px)';
    mainContent.prepend(errorDiv);

    // Trigger animation
    setTimeout(() => {
        errorDiv.style.opacity = '1';
        errorDiv.style.transform = 'translateY(0)';
    }, 100);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        errorDiv.style.opacity = '0';
        errorDiv.style.transform = 'translateY(-20px)';
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}
