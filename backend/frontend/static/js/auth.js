// frontend/static/js/auth.js

// 공통: 인증 토큰 붙여서 fetch하는 함수
// 공통: 인증 토큰 붙여서 fetch하는 함수
// frontend/static/js/auth.js

// 공통: 인증 토큰 붙여서 fetch하는 함수
async function authFetch(url, options = {}) {
  const access =
    localStorage.getItem("access") ||
    localStorage.getItem("token");

  const headers = options.headers ? { ...options.headers } : {};

  if (access) {
    headers["Authorization"] = `Bearer ${access}`;
  }

  // body가 FormData인지 체크
  const isFormData = options.body instanceof FormData;

  return fetch(url, {
    ...options,
    headers: isFormData
      ? {
          // ✅ FormData일 때는 Content-Type 직접 지정하지 않는다
          // 브라우저가 boundary 붙여서 multipart/form-data로 자동 설정해야 파일이 정상 전송됨
          ...headers,
        }
      : {
          // JSON 요청일 때만 application/json
          "Content-Type": "application/json",
          ...headers,
        },
  });
}


document.addEventListener("DOMContentLoaded", () => {
  // 1) 로그인 폼 처리
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    const loginError = document.getElementById("loginError");
    const usernameInput = document.getElementById("usernameInput");
    const passwordInput = document.getElementById("passwordInput");

    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      loginError.style.color = "red";
      loginError.textContent = "";

      const login_id = usernameInput.value.trim();
      const password = passwordInput.value;

      if (!login_id || !password) {
        loginError.textContent = "아이디와 비밀번호를 모두 입력해주세요.";
        return;
      }

      try {
        const response = await fetch("/api/auth/login/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ login_id, password }),
        });

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          loginError.textContent =
            data.detail || "아이디 또는 비밀번호가 올바르지 않습니다.";
          return;
        }

        const data = await response.json();

        // 🔥 백엔드 응답 구조에 맞게 토큰 저장
        // MemberLoginAPIView 가 access_token 키로 JWT를 내려준다.
        if (data.access_token) {
          localStorage.setItem("access", data.access_token);
        }

        // 혹시 나중에 DRF SimpleJWT 등으로 바뀌어 "access" 가 올 수도 있으니 같이 처리
        if (data.access) {
          localStorage.setItem("access", data.access);
        }

        // 기존에 쓸 수도 있는 값들 그대로 유지 (필요 없으면 나중에 제거 가능)
        if (data.refresh) {
          localStorage.setItem("refresh", data.refresh);
        }
        if (data.token) {
          localStorage.setItem("token", data.token);
        }

        loginError.style.color = "green";
        loginError.textContent = "로그인 성공! 메인 페이지로 이동합니다.";

        // 메인(레시피 목록) 페이지로 이동
        setTimeout(() => {
          window.location.href = "/";
        }, 500);
      } catch (err) {
        console.error("Login error:", err);
        loginError.textContent =
          "로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      }
    });
  }

  // 2) 메인 페이지: 레시피 목록 로딩
  const recipeListEl = document.getElementById("recipeList");
  if (recipeListEl) {
    loadRecipeList(recipeListEl);
  }

  // 3) "레시피 둘러보기" 버튼 클릭 시 인기 레시피 제목까지 스크롤
  const scrollBtn = document.getElementById("scrollToPopularBtn");
  const titleEl = document.querySelector("#popular-recipes .section-header h2");

  if (scrollBtn && titleEl) {
    scrollBtn.addEventListener("click", () => {
      const y =
        titleEl.getBoundingClientRect().top +
        window.pageYOffset -
        80; // 헤더 높이 만큼 보정
      window.scrollTo({ top: y, behavior: "smooth" });
    });
  }

  // 4) 레시피 상세 페이지라면 상세 불러오기
  const detailSection = document.querySelector(".recipe-detail-container");
  if (detailSection) {
    const recipeId = detailSection.dataset.recipeId;
    const detailContainer = document.getElementById("recipeDetail");
    if (recipeId && detailContainer) {
      loadRecipeDetail(recipeId, detailContainer);
    }
  }

  // 5) 관리자 메뉴 노출 여부 결정
  const adminNavLink = document.getElementById("adminNavLink");
  const token =
    localStorage.getItem("access") ||
    localStorage.getItem("token");

  if (adminNavLink && token) {
    authFetch("/api/auth/me/")
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data) => {
        if (!data) return;

        const role =
          data.role ||
          data.user_role ||
          data.member_role ||
          null;

        if (role === "ADMIN") {
          adminNavLink.style.display = "inline-flex";
        }
      })
      .catch((err) => console.error("me error:", err));
  }
});

// 레시피 목록 불러오기
async function loadRecipeList(container) {
  const errorEl = document.getElementById("recipeError");
  if (errorEl) errorEl.textContent = "";

  try {
    const response = await authFetch("/api/recipes/");

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        if (errorEl) {
          errorEl.textContent = "로그인이 필요합니다. 로그인 페이지로 이동합니다.";
        }
        setTimeout(() => {
          window.location.href = "/login/";
        }, 800);
        return;
      }

      if (errorEl) {
        errorEl.textContent = "레시피 목록을 불러오지 못했습니다.";
      }
      return;
    }

    const data = await response.json();

    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = "<p>등록된 레시피가 없습니다.</p>";
      return;
    }

    container.innerHTML = "";

    data.forEach((recipe) => {
      const {
        recipe_id,
        title,
        description,
        author_name,
        image_path,
        avg_rating,
        like_count,
      } = recipe;

      const card = document.createElement("article");
      card.className = "recipe-card";
      card.innerHTML = `
        <a href="/recipes/${recipe_id}/" class="recipe-link">
          <div class="recipe-thumb">
            ${
              image_path
                ? `<img src="${image_path}" alt="${title}">`
                : `<div class="placeholder-thumb">이미지 없음</div>`
            }
          </div>
          <div class="recipe-info">
            <h3 class="recipe-title">${title}</h3>
            <p class="recipe-desc">${description || ""}</p>
            <div class="recipe-meta">
              <span class="recipe-author">${author_name || "알 수 없음"}</span>
              <span class="recipe-rating">⭐ ${avg_rating ?? "-"}</span>
              <span class="recipe-likes">♥ ${like_count ?? 0}</span>
            </div>
          </div>
        </a>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    const errorEl2 = document.getElementById("recipeError");
    if (errorEl2) {
      errorEl2.textContent = "레시피 데이터를 불러오는 중 오류가 발생했습니다.";
    }
  }
}

// 레시피 상세 페이지 로딩
async function loadRecipeDetail(recipeId, container) {
  const errorEl = document.getElementById("recipeDetailError");
  if (errorEl) errorEl.textContent = "";

  try {
    const response = await authFetch(`/api/recipes/${recipeId}/`);

    if (!response.ok) {
      if (response.status === 404 && errorEl) {
        errorEl.textContent = "해당 레시피를 찾을 수 없습니다.";
        container.innerHTML = "";
        return;
      }
      if ((response.status === 401 || response.status === 403) && errorEl) {
        errorEl.textContent = "로그인이 필요합니다. 로그인 페이지로 이동합니다.";
        setTimeout(() => (window.location.href = "/login/"), 800);
        return;
      }
      if (errorEl) errorEl.textContent = "레시피 정보를 불러오지 못했습니다.";
      return;
    }

    const recipe = await response.json();

    const {
      recipe_id: id,
      title,
      description,
      author_name,
      image_path,
      avg_rating,
      like_count,
      cooking_time,
      ingredients,
      tags,
    } = recipe;

    container.innerHTML = `
      <article class="recipe-detail">
        <div class="recipe-detail-header">
          <h2 class="recipe-detail-title">${title}</h2>
          <div class="recipe-detail-meta">
            <span class="recipe-detail-author">${author_name || "알 수 없음"}</span>
            <span class="recipe-detail-rating">⭐ ${avg_rating ?? "-"}</span>
            <span class="recipe-detail-likes">♥ ${like_count ?? 0}</span>
            ${
              cooking_time
                ? `<span class="recipe-detail-time">${cooking_time}분</span>`
                : ""
            }
          </div>
        </div>

        <div class="recipe-detail-body">
          <div class="recipe-detail-image">
            ${
              image_path
                ? `<img src="${image_path}" alt="${title}">`
                : `<div class="placeholder-thumb">이미지 없음</div>`
            }
          </div>
          <div class="recipe-detail-info">
            <h3>설명</h3>
            <p>${description || ""}</p>

            ${
              ingredients
                ? `
              <h3>재료</h3>
              <ul class="recipe-ingredients">
                ${ingredients.map((ing) => `<li>${ing}</li>`).join("")}
              </ul>
            `
                : ""
            }

            ${
              tags
                ? `
              <h3>태그</h3>
              <div class="recipe-tags">
                ${tags.map((t) => `<span class="tag">#${t}</span>`).join("")}
              </div>
            `
                : ""
            }
          </div>
        </div>
      </article>
    `;
  } catch (err) {
    console.error(err);
    if (errorEl) {
      errorEl.textContent = "레시피 정보를 불러오는 중 오류가 발생했습니다.";
    }
  }
}
