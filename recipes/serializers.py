from rest_framework import serializers
from .models import (
    Member,
    Recipe,
    RecipeTag,
    Tag,
    RecipeStep,
    RecipeIngredient,
    Ingredient,
    RecipeComment,
)


class MemberSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('member_id', 'login_id', 'name', 'role')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('tag_id', 'name')


class IngredientAmountSerializer(serializers.ModelSerializer):
    ingredient = serializers.CharField(source='ingredient.name')

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ('step_id', 'step_order', 'content')


class RecipeListSerializer(serializers.ModelSerializer):
    author = MemberSimpleSerializer(read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'recipe_id',
            'title',
            'author',
            'avg_score',
            'rating_count',
            'image_path',
            'created_at',
            'tags',
        )

    def get_tags(self, obj):
        # models.py에서 RecipeTag.related_name='recipe_tags', Tag.related_name='tag_recipes' 로 가정
        tag_objs = [rt.tag for rt in obj.recipe_tags.all()]
        return TagSerializer(tag_objs, many=True).data


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = MemberSimpleSerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    steps = RecipeStepSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'recipe_id',
            'title',
            'author',
            'description',
            'cooking_time',
            'image_path',
            'created_at',
            'updated_at',
            'avg_score',
            'rating_count',
            'tags',
            'steps',
            'ingredients',
        )

    def get_tags(self, obj):
        tag_objs = [rt.tag for rt in obj.recipe_tags.all()]
        return TagSerializer(tag_objs, many=True).data

    def get_ingredients(self, obj):
        # recipe.recipe_ingredients → RecipeIngredient 쿼리셋
        ri_qs = obj.recipe_ingredients.all()
        return IngredientAmountSerializer(ri_qs, many=True).data


class RecipeCommentSerializer(serializers.ModelSerializer):
    author = MemberSimpleSerializer(read_only=True)

    class Meta:
        model = RecipeComment
        fields = (
            'comment_id',
            'author',
            'content',
            'created_at',
            'parent_comment',
        )
