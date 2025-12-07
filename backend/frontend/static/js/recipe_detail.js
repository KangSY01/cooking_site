document.addEventListener("DOMContentLoaded", () => {
  const pageEl = document.getElementById("recipeDetailPage");
  const recipeId = pageEl.dataset.recipeId;

  const token = localStorage.getItem("accessToken");
  let currentMemberId = null;  // 내 댓글 삭제 여부 판단용

  // ====== 공통 DOM ======
  const titleEl = document.getElementById("recipeTitle");
  const subEl = document.getElementById("recipeSubtitle");
  const authorEl = document.getElementById("recipeAuthor");
  const timeEl = document.getElementById("recipeTime");
  const tagsEl = document.getElementById("recipeTags");
  const imageEl = document.getElementById("recipeImage");
  const avgScoreEl = document.getElementById("recipeAvgScore");
  const ratingCountEl = document.getElementById("recipeRatingCount");
  const likeCountEl = document.getElementById("recipeLikeCount");
  const ingredientListEl = document.getElementById("ingredientList");
  const stepListEl = document.getElementById("stepList");
  const commentListEl = document.getElementById("commentList");
  const commentCountEl = document.getElementById("commentCount");
  const commentInput = document.getElementById("commentInput");
  const commentSubmitBtn = document.getElementById("commentSubmitBtn");

  // ====== 1) 내 정보 불러오기 (댓글 삭제/표시용) ======
  if (token) {
    fetch("/api/auth/me/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.member_id) {
          currentMemberId = data.member_id;
        }
      })
      .catch(() => {});
  }

  // ====== 2) 레시피 상세 데이터 불러오기 ======
  async function loadRecipeDetail() {
    try {
      const res = await fetch(`/api/recipes/${recipeId}/`);
      const data = await res.json();
      if (!res.ok) {
        console.error("레시피 상세 실패", data);
        return;
      }

      // 여기서 data 구조는 너의 RecipeDetailSerializer에 맞게 약간 수정할 수 있음
      titleEl.textContent = data.title || "";
      subEl.textContent = data.description || "";
      authorEl.textContent = data.author_name ? `작성자: ${data.author_name}` : "";
      if (data.cooking_time) {
        timeEl.textContent = `⏱ ${data.cooking_time}분`;
      }

      // 대표 이미지
      if (data.image_path) {
        imageEl.src = data.image_path;
      } else {
        imageEl.src = "https://via.placeholder.com/960x400?text=No+Image";
      }

      // 태그
      tagsEl.innerHTML = "";
      const tags = data.tags || [];  // ["한식","간단","매운맛"] 같은 형태라고 가정
      tags.forEach(tag => {
        const pill = document.createElement("span");
        pill.className = "recipe-tag-pill";
        pill.textContent = `#${tag}`;
        tagsEl.appendChild(pill);
      });

      // 평점 / 좋아요
      if (typeof data.avg_score !== "undefined" && data.avg_score !== null) {
        avgScoreEl.textContent = data.avg_score.toFixed
          ? data.avg_score.toFixed(1)
          : data.avg_score;
      }
      ratingCountEl.textContent = data.rating_count
        ? `${data.rating_count}명 평가`
        : "0명 평가";
      likeCountEl.textContent = data.like_count ?? 0;

      // 재료
      ingredientListEl.innerHTML = "";
      const ingredients = data.ingredients || []; // [{name, amount}, ...]
      ingredients.forEach(ing => {
        const li = document.createElement("li");
        li.className = "ingredient-item";
        li.innerHTML = `
          <span>${ing.name}</span>
          <span>${ing.amount || ""}</span>
        `;
        ingredientListEl.appendChild(li);
      });

      // 단계
      stepListEl.innerHTML = "";
      const steps = data.steps || []; // [{step_order, content}, ...]
      steps
        .sort((a, b) => (a.step_order || 0) - (b.step_order || 0))
        .forEach(step => {
          const li = document.createElement("li");
          li.className = "step-item";
          li.innerHTML = `
            <div class="step-badge">${step.step_order}</div>
            <div>${step.content}</div>
          `;
          stepListEl.appendChild(li);
        });

    } catch (err) {
      console.error(err);
    }
  } // ✅ 누락되었던 함수 닫는 중괄호 추가

  // ====== 3) 댓글 목록 불러오기 ======
  async function loadComments() {
    try {
      const res = await fetch(`/api/recipes/${recipeId}/comments/`);
      const data = await res.json();
      if (!res.ok) {
        console.error("댓글 목록 실패", data);
        return;
      }

      const comments = Array.isArray(data) ? data : data.results || [];
      commentCountEl.textContent = `(${comments.length})`;
      commentListEl.innerHTML = "";

      comments.forEach(comment => {
        const item = document.createElement("div");
        item.className = "comment-item";

        const canDelete =
          currentMemberId && comment.author_id === currentMemberId;

        item.innerHTML = `
          <div class="comment-avatar">👤</div>
          <div class="comment-body">
            <div class="comment-meta">
              <div>
                <span class="comment-author">${comment.author_name || "익명"}</span>
                <span class="comment-date">${formatDate(comment.created_at)}</span>
              </div>
              ${
                canDelete
                  ? `<span class="comment-delete" data-comment-id="${comment.comment_id}">삭제</span>`
                  : ""
              }
            </div>
            <div class="comment-content">${escapeHtml(comment.content || "")}</div>
          </div>
        `;
        commentListEl.appendChild(item);
      });
    } catch (err) {
      console.error(err);
    }
  }

  function formatDate(isoString) {
    if (!isoString) return "";
    const d = new Date(isoString);
    return `${d.getFullYear()}.${d.getMonth() + 1}.${d.getDate()}`;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
  }

  // ====== 4) 댓글 작성 (로그인 필요) ======
  function ensureLoginOrRedirect() {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      alert("로그인 후 댓글을 작성할 수 있습니다.");
      localStorage.setItem("nextUrl", window.location.pathname);
      window.location.href = "/login/";
      return false;
    }
    return true;
  }

  // ========= 초기 로드 =========
  console.log("recipe detail page, recipeId =", recipeId);
  loadRecipeDetail();
  loadComments();

  // 포커스만 해도 로그인 체크 (요구사항)
  if (commentInput) {
    commentInput.addEventListener("focus", () => {
      ensureLoginOrRedirect();
    });
  }

  // 버튼 클릭 시 댓글 작성
  if (commentSubmitBtn && commentInput) {
    commentSubmitBtn.addEventListener("click", async () => {
      if (!ensureLoginOrRedirect()) return;

      const token = localStorage.getItem("accessToken");
      const content = commentInput.value.trim();
      if (!content) {
        alert("댓글 내용을 입력해주세요.");
        return;
      }

      try {
        const res = await fetch(`/api/recipes/${recipeId}/comments/create/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          console.error("댓글 작성 실패", data);
          alert("댓글 작성에 실패했습니다.");
          return;
        }

        commentInput.value = "";
        await loadComments();
      } catch (err) {
        console.error(err);
        alert("서버와 통신 중 오류가 발생했습니다.");
      }
    });
  }

  // ====== 5) 댓글 삭제 (내 댓글만) ======
  if (commentListEl) {
    commentListEl.addEventListener("click", async (e) => {
      if (!e.target.classList.contains("comment-delete")) return;
      if (!ensureLoginOrRedirect()) return;

      const commentId = e.target.dataset.commentId;
      if (!commentId) return;

      if (!confirm("댓글을 삭제하시겠습니까?")) return;

      const token = localStorage.getItem("accessToken");

      try {
        const res = await fetch(`/api/comments/${commentId}/`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok && res.status !== 204) {
          console.error("댓글 삭제 실패", res.status);
          alert("댓글 삭제에 실패했습니다.");
          return;
        }

        await loadComments();
      } catch (err) {
        console.error(err);
        alert("서버와 통신 중 오류가 발생했습니다.");
      }
    });
  }

  // 브레드크럼 클릭 시 메인으로
  const breadcrumb = document.querySelector(".breadcrumb");
  if (breadcrumb) {
    breadcrumb.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

});