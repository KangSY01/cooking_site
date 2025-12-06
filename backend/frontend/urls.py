from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path("recipes/<int:recipe_id>/", views.recipe_detail_page, name="recipe-detail-page"),
]
