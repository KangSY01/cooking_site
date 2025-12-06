document.addEventListener("DOMContentLoaded", () => {
  setAuthUI();

  const loginBtn = document.getElementById("loginButton");
  const logoutBtn = document.getElementById("logoutButton");
  const loginForm = document.getElementById("loginForm");

  if (loginBtn) {
    loginBtn.addEventListener("click", () => {
      window.location.href = "/login/";
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      setAuthUI();
      window.location.href = "/";
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("usernameInput").value;
      const password = document.getElementById("passwordInput").value;
      const errorEl = document.getElementById("loginError");

      try {
        const res = await fetch(`${API_BASE}/token/`, {   // ← 네 로그인 엔드포인트로 수정 가능
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            login_id: login_id,
            password: password,
          }),
        });

        if (!res.ok) {
          errorEl.textContent = "로그인 실패. 아이디/비밀번호를 확인해주세요.";
          return;
        }

        const data = await res.json();
        localStorage.setItem("access_token", data.access);
        setAuthUI();
        window.location.href = "/";
      } catch (err) {
        console.error(err);
        errorEl.textContent = "네트워크 오류가 발생했습니다.";
      }
    });
  }
});
