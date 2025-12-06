const token = localStorage.getItem("token");
const recipeId = window.location.pathname.split("/")[2]; 
// 예: /recipes/5/edit/ → ["", "recipes", "5", "edit"]

async function loadRecipeForEdit() {
    const res = await fetch(`/api/recipes/${recipeId}/`, {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!res.ok) {
        alert("레시피 정보를 불러올 수 없습니다.");
        return;
    }

    const data = await res.json();

    // 기본 필드 채우기
    document.getElementById("titleInput").value = data.title;
    document.getElementById("descriptionInput").value = data.description;

    // 재료 불러오기
    const ingredientContainer = document.getElementById("ingredientList");
    ingredientContainer.innerHTML = "";
    data.ingredients.forEach((item) => {
        addIngredientField(item.name);
    });

    // 조리 단계 불러오기
    const stepContainer = document.getElementById("stepList");
    stepContainer.innerHTML = "";
    data.steps.forEach((item) => {
        addStepField(item.description);
    });

    // 이미지 표시
    document.getElementById("currentImage").src = data.image;
}

loadRecipeForEdit();
