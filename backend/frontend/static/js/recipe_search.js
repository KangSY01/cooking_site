// frontend/static/js/recipe_search.js

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recipeSearchForm");
  const keywordInput = document.getElementById("keywordInput");
  const resultsContainer = document.getElementById("searchResults");
  const resultCountEl = document.getElementById("searchResultCount");
  const errorEl = document.getElementById("searchError");

  if (!form || !keywordInput || !resultsContainer) return;

  // 페이지 처음 들어왔을 때 전체 레시피 보여주고 싶으면 여기서 한번 호출
  // searchRecipes("");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const keyword = keywordInput.value.trim();
    searchRecipes(keyword);
  });
});

async function searchRecipes(keyword) {
  const resultsContainer = document.getElementById("searchResults");
  const resultCountEl = document.getElementById("searchResultCount");
  const errorEl = document.getElementById("searchError");

  if (!resultsContainer) return;

  if (errorEl) errorEl.textContent = "";
  if (resultCountEl) resultCountEl.textContent = "";

  // 기본 /api/recipes/ 에 ?search= 키워드 붙여서 사용한다고 가정
  let url = "/api/recipes/";
  if (keyword) {
    const params = new URLSearchParams({ search: keyword });
    url += "?" + params.toString();
  }

  try {
    const response = await fetch(url);  // 로그인 필요 없음

    if (!response.ok) {
      if (errorEl) errorEl.textContent = "레시피 검색에 실패했습니다.";
      resultsContainer.innerHTML = "";
      return;
    }

    const data = await response.json();

    if (!Array.isArray(data) || data.length === 0) {
      resultsContainer.innerHTML = "<p>검색 결과가 없습니다.</p>";
      if (resultCountEl) resultCountEl.textContent = "검색 결과 0개";
      return;
    }

    // 카드 렌더링 부분만 교체
resultsContainer.innerHTML = "";
data.forEach((recipe) => {
  const {
    recipe_id,
    title,
    description,
    author_name,
    image_path,
    avg_rating,
    like_count,
    cooking_time,
    tags,
  } = recipe;

  // tags가 ["한식", "매운맛"] OR [{name: "한식"}, {name: "매운맛"}] 둘 다 대응
  const tagNames = (tags || [])
    .map((t) => {
      if (typeof t === "string") return t;
      if (t && typeof t === "object") {
        return t.name || t.tag_name || t.label || "";
      }
      return "";
    })
    .filter(Boolean);

  const ratingText =
    typeof avg_rating === "number"
      ? avg_rating.toFixed(1)
      : avg_rating || "-";

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
        <span class="rating-badge">
          ⭐ ${ratingText}
        </span>
      </div>
      <div class="recipe-info">
        <h3 class="recipe-title">${title}</h3>
        <p class="recipe-desc">${description || ""}</p>
        <div class="recipe-meta">
          ${
            cooking_time
              ? `<span class="recipe-time">⏱ ${cooking_time}분</span>`
              : "<span></span>"
          }
          <span class="recipe-likes">♥ ${like_count ?? 0}</span>
        </div>
        ${
          tagNames.length
            ? `
          <div class="recipe-tags">
            ${tagNames.map((name) => `<span class="tag">#${name}</span>`).join("")}
          </div>
        `
            : ""
        }
      </div>
    </a>
  `;

  resultsContainer.appendChild(card);
});


    if (resultCountEl) {
      resultCountEl.textContent = `검색 결과 ${data.length}개`;
    }
  } catch (err) {
    console.error("Search error:", err);
    if (errorEl) {
      errorEl.textContent = "검색 중 오류가 발생했습니다.";
    }
  }
}
