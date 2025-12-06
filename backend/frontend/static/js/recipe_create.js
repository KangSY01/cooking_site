// 재료 추가
document.getElementById("addIngredientBtn").addEventListener("click", () => {
  const list = document.getElementById("ingredientList");

  const row = document.createElement("div");
  row.className = "ingredient-row";
  row.innerHTML = `
    <input class="form-input" placeholder="재료명">
    <input class="form-input small" placeholder="양">
    <button type="button" class="row-remove-btn">✕</button>
  `;

  list.appendChild(row);
});

// 조리 단계 추가
document.getElementById("addStepBtn").addEventListener("click", () => {
  const list = document.getElementById("stepList");
  const stepNum = list.children.length + 1;

  const row = document.createElement("div");
  row.className = "step-row";
  row.innerHTML = `
    <span class="step-badge">${stepNum}</span>
    <input class="form-input" placeholder="조리 단계를 입력하세요">
    <button type="button" class="row-remove-btn">✕</button>
  `;

  list.appendChild(row);
});

// 재료/단계 행 삭제 (이벤트 위임)
document.getElementById("ingredientList").addEventListener("click", (e) => {
  if (e.target.classList.contains("row-remove-btn")) {
    const row = e.target.closest(".ingredient-row");
    if (row) row.remove();
  }
});

document.getElementById("stepList").addEventListener("click", (e) => {
  if (e.target.classList.contains("row-remove-btn")) {
    const row = e.target.closest(".step-row");
    if (row) {
      row.remove();
      renumberSteps();
    }
  }
});

// 단계 번호 재정렬
function renumberSteps() {
  const badges = document.querySelectorAll("#stepList .step-badge");
  badges.forEach((badge, index) => {
    badge.textContent = index + 1;
  });
}
