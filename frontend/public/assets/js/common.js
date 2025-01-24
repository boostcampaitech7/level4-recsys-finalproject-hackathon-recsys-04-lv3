// 공통 헤더/푸터 로드
window.addEventListener('DOMContentLoaded', () => {
    // 헤더 로드
    fetch('../components/header.html')
      .then(res => {
        if (!res.ok) throw new Error("헤더를 불러올 수 없습니다.");
        return res.text();
      })
      .then(data => {
        document.body.insertAdjacentHTML('afterbegin', data);
        setActiveNav();
        setupLogout();
      })
      .catch(error => console.error(error));

    // 푸터 로드
    fetch('../components/footer.html')
      .then(res => {
        if (!res.ok) throw new Error("푸터를 불러올 수 없습니다.");
        return res.text();
      })
      .then(data => {
        document.body.insertAdjacentHTML('beforeend', data);
      })
      .catch(error => console.error(error));

    // 토큰 검증 (로그인 페이지 제외)
    if (!window.location.pathname.includes('login.html')) {
      validateToken();
    }
  });

  // 토큰 검증 함수
  async function validateToken() {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = 'login.html';
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/validate", {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('토큰이 유효하지 않습니다.');
      }
    } catch (error) {
      localStorage.removeItem('token');
      window.location.href = 'login.html';
    }
  }

  // 로그아웃 기능
  function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        window.location.href = 'login.html';
      });
    }
  }

  // 활성 메뉴 표시
  function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop();
    document.querySelectorAll('.header a').forEach(link => {
      const linkPage = link.getAttribute('href');
      if (linkPage === currentPage) {
        link.classList.add('active');
      }
    });
  }
