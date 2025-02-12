document.addEventListener("DOMContentLoaded", function () {
    loadComponent("header", "components/header.html", highlightActiveNav);
    loadComponent("footer", "components/footer.html");
});

function loadComponent(elementId, filePath, callback = null) {
    fetch(filePath)
        .then(response => response.text())
        .then(data => {
            document.getElementById(elementId).innerHTML = data;
            if (callback) callback(); // 헤더 로드 후 실행
        })
        .catch(error => console.error(`Error loading ${filePath}:`, error));
}

function highlightActiveNav() {
    const currentPath = window.location.pathname.split("/").pop(); // 현재 페이지 파일명

    // 페이지 파일명과 네비게이션 메뉴 href 매핑
    const pageToNavMap = {
        "main.html": "화이트보드",
        "new_note.html": "업로드",
        "notes.html": "노트 보관함",
        "quiz.html": "퀴즈",
        "feedback.html": "피드백 보관함",
        "mypage.html": "마이페이지"
    };

    const navLinks = document.querySelectorAll(".header .left a, .header .right a");

    navLinks.forEach(link => {
        if (pageToNavMap[currentPath] === link.textContent.trim()) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}
