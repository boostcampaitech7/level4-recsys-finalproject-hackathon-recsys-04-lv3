document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;
    const history = [];
    const redoStack = [];
    let currentTool = 'pen';

    // Canvas 크기 설정
    function resizeCanvas() {
        const container = canvas.parentElement;
        canvas.width = container.clientWidth - 2;
        canvas.height = 600;

        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // 초기 설정
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    saveState();

    // 도구 설정
    function setTool(tool) {
        currentTool = tool;
        if (tool === 'pen') {
            ctx.strokeStyle = 'black';
            ctx.lineWidth = 2;
        } else {
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 20;
        }
        ctx.lineCap = 'round';
    }

    // 상태 저장
    function saveState() {
        history.push(canvas.toDataURL());
        redoStack.length = 0;
        updateButtons();
    }

    // 버튼 상태 업데이트
    function updateButtons() {
        document.getElementById('undoBtn').disabled = history.length <= 1;
        document.getElementById('redoBtn').disabled = redoStack.length === 0;
    }

    // 그리기 시작
    function startDrawing(e) {
        isDrawing = true;
        const coords = getCoordinates(e);
        [lastX, lastY] = [coords.x, coords.y];
    }

    // 그리기
    function draw(e) {
        if (!isDrawing) return;
        e.preventDefault();

        const coords = getCoordinates(e);
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
        [lastX, lastY] = [coords.x, coords.y];
    }

    // 그리기 종료
    function stopDrawing() {
        if (isDrawing) {
            isDrawing = false;
            saveState();
        }
    }

    // 좌표 얻기
    function getCoordinates(e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        if (e.touches && e.touches[0]) {
            return {
                x: (e.touches[0].clientX - rect.left) * scaleX,
                y: (e.touches[0].clientY - rect.top) * scaleY
            };
        }

        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }

    function undo() {
        if (history.length > 1) {
            redoStack.push(history.pop());
            const img = new Image();
            img.src = history[history.length - 1];
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                updateButtons();
            };
        }
    }

    function redo() {
        if (redoStack.length > 0) {
            const img = new Image();
            img.src = redoStack[redoStack.length - 1];
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                history.push(redoStack.pop());
                updateButtons();
            };
        }
    }

    function clearCanvas() {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'black';
        saveState();
    }

    // 이벤트 리스너
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    canvas.addEventListener('touchstart', startDrawing);
    canvas.addEventListener('touchmove', draw);
    canvas.addEventListener('touchend', stopDrawing);

    document.getElementById('penBtn').addEventListener('click', (e) => {
        setTool('pen');
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
    });

    document.getElementById('eraserBtn').addEventListener('click', (e) => {
        setTool('eraser');
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
    });

    document.getElementById('undoBtn').addEventListener('click', undo);
    document.getElementById('redoBtn').addEventListener('click', redo);
    document.getElementById('clearBtn').addEventListener('click', clearCanvas);

    document.getElementById('downloadBtn').addEventListener('click', () => {
        const title = document.getElementById('noteTitle').value;
        const fileName = title ? `${title}.png` : 'drawing.png';

        const link = document.createElement('a');
        link.download = fileName;
        link.href = canvas.toDataURL();
        link.click();
    });

    document.getElementById('submitBtn').addEventListener('click', async () => {
        const title = document.getElementById('noteTitle').value;
        const subject = document.getElementById('subjectSelect').value;
        const loadingOverlay = document.getElementById('loading-overlay');

        // 입력 검증
        if (!subject) {
            alert('과목을 선택해주세요.');
            return;
        }
        if (!title) {
            alert('노트 제목을 입력해주세요.');
            return;
        }

        // 로딩 화면 표시
        loadingOverlay.classList.add('active');

        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            const file = new File([blob], 'drawing.png', { type: 'image/png' });

            formData.append('file', file);
            formData.append('title', title);
            formData.append('subjects_id', subject);
            formData.append('user_id', localStorage.getItem('user_id'));

            try {
                const token = localStorage.getItem('token');
                const response = await fetch('http://localhost:8000/api/v1/note/upload', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                console.log('서버 응답:', data);
                alert('노트가 성공적으로 저장되었습니다.');
                window.location.href = 'notes.html';
            } catch (error) {
                console.error('Error:', error);
                alert('노트 저장에 실패했습니다. 에러: ' + error.message);
            } finally {
                // 로딩 화면 숨김
                loadingOverlay.classList.remove('active');
            }
        }, 'image/png');
    });

    setTool('pen');
});

// userNameContainer 에 사용자 이름 local strage에서 가져와서 넣어주기
document.addEventListener('DOMContentLoaded', function () {
    const userName = localStorage.getItem('userEmail');
    if (userName) {
        document.getElementById('userNameContainer').textContent = userName;
    }
});
