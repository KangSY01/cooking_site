from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path("recipes/<int:recipe_id>/", views.recipe_detail_view, name="recipe_detail_view"),
    path("mypage/", views.mypage, name="mypage"),
    path("recipes/new/", views.recipe_create_page, name="recipe-create"),
    path("signup/", views.signup_view, name="signup"),
    path("recipes/search/", views.recipe_search_page, name="recipe-search"),
    path("dashboard/admin/", views.admin_dashboard_page, name="admin-dashboard"),
    path("recipes/<int:recipe_id>/edit/", views.recipe_edit_page, name="recipe_edit"),
]
