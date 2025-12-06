from django.contrib.auth.hashers import make_password, check_password
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

# ============================
# 회원가입 / 로그인 Serializer
# ============================

class MemberSignupSerializer(serializers.ModelSerializer):
    # password는 입력만 받도록 write_only
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Member
        # role은 클라이언트가 안 보내도 되게 하고, 서버에서 기본값으로 넣어줄 거라
        # fields에 포함하지 않는다.
        fields = ["member_id", "login_id", "password", "name"]
        read_only_fields = ["member_id"]

    def create(self, validated_data):
        raw_password = validated_data.pop("password")

        # role은 여기서 서버가 강제로 지정 (일반 사용자)
        member = Member(
            login_id=validated_data["login_id"],
            name=validated_data["name"],
            role="GOURMET",  # COOK/ADMIN은 나중에 관리자 도구로 변경
        )
        # 비밀번호는 해시해서 저장
        member.password = make_password(raw_password)
        member.save()
        return member


class MemberLoginSerializer(serializers.Serializer):
    login_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_id = attrs.get("login_id")
        password = attrs.get("password")

        try:
            member = Member.objects.get(login_id=login_id)
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 로그인 아이디입니다.")

        # 해시된 비밀번호 비교
        if not check_password(password, member.password):
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")

        attrs["member"] = member
        return attrs