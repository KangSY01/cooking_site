from django.contrib import admin

# Register your models here.
from .models import Member, Recipe, Ingredient, Tag, RecipeComment


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'login_id', 'name', 'role', 'created_at')
    search_fields = ('login_id', 'name')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe_id', 'title', 'author', 'created_at', 'avg_score', 'rating_count')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)
    raw_id_fields = ('author',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('ingredient_id', 'name')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_id', 'name')
    search_fields = ('name',)


@admin.register(RecipeComment)
class RecipeCommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'recipe', 'author', 'created_at')
    search_fields = ('content',)
    raw_id_fields = ('recipe', 'author', 'parent_comment')
