const token =
  localStorage.getItem("access") ||
  localStorage.getItem("token");

const pathParts = window.location.pathname.split("/").filter(Boolean);
const recipeId = pathParts[1];   // /recipes/4/ → 4

document.getElementById("deleteRecipeBtn").addEventListener("click", async () => {
  if (!confirm("정말 이 레시피를 삭제할까요?")) return;

  const res = await fetch(`/api/recipes/${recipeId}/`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  if (res.status === 204) {
    alert("삭제되었습니다.");
    window.location.href = "/";
  } else {
    const data = await res.json().catch(() => ({}));
    alert(data.detail || "삭제 중 오류가 발생했습니다.");
  }
});
