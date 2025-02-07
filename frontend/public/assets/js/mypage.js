document.addEventListener('DOMContentLoaded', async () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    showLoadingState();

    try {
        const [userResponse, noteCountResponse, oxCountResponse, multipleCountResponse, activatelogResponse] = await Promise.all([
            fetch(`http://localhost:8000/api/v1/auth/user/${userId}`),
            fetch(`http://localhost:8000/api/v1/note/count/${userId}`),
            fetch(`http://localhost:8000/api/v1/quiz/ox-statistics/${userId}`),
            fetch(`http://localhost:8000/api/v1/quiz/multiple-statistics/${userId}`),
            fetch(`http://localhost:8000/api/v1/note/activate-log/${userId}`)
        ]);

        const userData = await userResponse.json();
        const noteCount = await noteCountResponse.json();
        const oxCount = await oxCountResponse.json();
        const multipleCount = await multipleCountResponse.json();
        const activate = await activatelogResponse.json();

        renderUserProfile(userData);
        renderStats(noteCount, oxCount, multipleCount);
        renderContributionGraph(activate);

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

function renderStats(noteCount, oxCount, multipleCount) {
    const stats = [
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

        <div class="stat-card pie-chart-container">
            <h3>OX 퀴즈</h3>
            <canvas id="oxPieChart"></canvas>
        </div>

        <div class="stat-card pie-chart-container">
            <h3>4지선다 퀴즈</h3>
            <canvas id="multiplePieChart"></canvas>
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
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 10,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });

    const ox = document.getElementById('oxPieChart').getContext('2d');
    new Chart(ox, {
        type: 'doughnut',
        data: {
            labels: oxCount.map(stat => stat.category),
            datasets: [{
                data: oxCount.map(stat => stat.count),
                backgroundColor: [ '#A2CFFF', '#FFB3A7', '#B8B8B8']
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 10,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });

    const mul = document.getElementById('multiplePieChart').getContext('2d');
    new Chart(mul, {
        type: 'doughnut',
        data: {
            labels: multipleCount.map(stat => stat.category),
            datasets: [{
                data: multipleCount.map(stat => stat.count),
                backgroundColor: [ '#A2CFFF', '#FFB3A7', '#B8B8B8']
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 10,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

function renderContributionGraph(activate) {
    const grid = document.getElementById('contributionGrid');
    const monthLabels = document.getElementById('monthLabels');
    const daysColumn = document.getElementById('daysColumn');

    grid.innerHTML = '';
    monthLabels.innerHTML = '';
    daysColumn.innerHTML = '';

    const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    const today = new Date();
    const contributions = activate;

    const startDayOfWeek = today.getDay();

    days.forEach(day => {
        const dayLabel = document.createElement('div');
        dayLabel.className = 'day-label';
        dayLabel.textContent = day;
        daysColumn.appendChild(dayLabel);
    });

    let totalWeeks = Math.ceil((364 + startDayOfWeek) / 7);

    for (let week = 0; week < totalWeeks; week++) {
        const column = document.createElement('div');
        column.className = 'contribution-column';

        for (let day = 0; day < 7; day++) {
            const index = week * 7 + day - startDayOfWeek;
            const date = new Date();
            date.setDate(today.getDate() - (364 - index));
            const level = index >= -startDayOfWeek ? contributions[index] || 0 : 0;

            const cell = document.createElement('div');
            cell.className = 'contribution-cell';
            cell.dataset.level = level;
            cell.dataset.date = date.toISOString().split('T')[0];
            cell.dataset.count = level;

            cell.addEventListener('mouseover', showTooltip);
            cell.addEventListener('mouseout', hideTooltip);

            column.appendChild(cell);
        }
        grid.appendChild(column);
    }
}

function showTooltip(event) {
    const tooltip = document.getElementById('tooltip');
    tooltip.textContent = `${event.target.dataset.date}: ${event.target.dataset.count}개`;
    tooltip.style.left = `${event.pageX + 10}px`;
    tooltip.style.top = `${event.pageY + 10}px`;
    tooltip.style.display = 'block';
}

function hideTooltip() {
    document.getElementById('tooltip').style.display = 'none';
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
