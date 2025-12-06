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