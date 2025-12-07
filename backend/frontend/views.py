from django.shortcuts import render

# Create your views here.

def login_page(request):
    return render(request, "login.html")

def home(request):
    return render(request, "recipes/list.html")

def mypage(request):
    # 일단 템플릿만 렌더링, 실제 데이터는 JS로 불러오게 할 예정
    return render(request, "mypage.html")

def recipe_create_page(request):
    return render(request, "recipes/recipe_create.html", {
        "is_edit": False,
        "recipe_id": None,
    })

def recipe_edit_page(request, recipe_id):
    return render(request, "recipes/recipe_create.html", {
        "is_edit": True,
        "recipe_id": recipe_id,
    })

def signup_view(request):
    return render(request, "signup.html")

def recipe_detail_view(request, recipe_id):
    # 템플릿 경로를 recipes/recipe_detail.html 로!
    return render(request, "recipes/recipe_detail.html", {
        "recipe_id": recipe_id
    })

def recipe_search_page(request):
    return render(request, "recipes/recipe_search.html")

def admin_dashboard_page(request):
    return render(request, "admin/admin_dashboard.html")
