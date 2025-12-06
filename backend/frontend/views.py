from django.shortcuts import render

# Create your views here.

def login_page(request):
    return render(request, "login.html")

def home(request):
    return render(request, "recipes/list.html")

def recipe_detail_page(request, recipe_id):
    # template에서 JS가 recipe_id를 이용해 /api/recipes/{id}/ 를 호출하게 할 것
    return render(request, "recipes/detail.html", {"recipe_id": recipe_id})

def mypage(request):
    # 일단 템플릿만 렌더링, 실제 데이터는 JS로 불러오게 할 예정
    return render(request, "mypage.html")

def recipe_create_page(request):
    # 새 레시피 등록 페이지
    return render(request, "recipes/recipe_create.html")

def signup_view(request):
    return render(request, "signup.html")

def recipe_detail_view(request, recipe_id):
    # 템플릿에서 recipe_id만 넘겨주고, 데이터는 JS에서 /api/... 로 가져옴
    return render(request, "recipe_detail.html", {"recipe_id": recipe_id})

def recipe_search_page(request):
    return render(request, "recipes/recipe_search.html")

def admin_dashboard_page(request):
    return render(request, "admin/admin_dashboard.html")