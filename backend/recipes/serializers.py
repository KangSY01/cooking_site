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
    Rating,
    RecipeSummary,
    Report,
)

class MemberMeSerializer(serializers.ModelSerializer):
    recipe_count = serializers.IntegerField(read_only=True)
    like_received_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Member
        fields = (
            "member_id",
            "login_id",
            "name",
            "created_at",
            "recipe_count",
            "like_received_count",
        )

class MyRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "recipe_id",
            "title",
            "description",
            "cooking_time",
            "image_path",
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
    
class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    레시피 생성/수정용 Serializer.
    - author 는 request.user 에서 자동 주입
    - tag_ids: 태그 id 리스트 (예: [1,2,3])
    """
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="태그 id 리스트 (예: [1,2,3])",
    )

    class Meta:
        model = Recipe
        fields = (
            'title',
            'description',
            'cooking_time',
            'image_path',
            'tag_ids',
        )

    def _set_tags(self, recipe, tag_ids):
        # 기존 태그 연결 삭제
        RecipeTag.objects.filter(recipe=recipe).delete()

        if not tag_ids:
            return

        # 유효한 태그만 조회해서 연결
        tag_qs = Tag.objects.filter(tag_id__in=tag_ids)
        recipe_tag_objs = [
            RecipeTag(recipe=recipe, tag=tag)
            for tag in tag_qs
        ]
        RecipeTag.objects.bulk_create(recipe_tag_objs)

    def create(self, validated_data):
        request = self.context['request']
        tag_ids = validated_data.pop('tag_ids', [])

        # author는 JWT 인증된 Member
        recipe = Recipe.objects.create(
            author=request.user,
            **validated_data,
        )
        self._set_tags(recipe, tag_ids)
        return recipe

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # tag_ids 가 들어온 경우에만 태그 갱신
        if tag_ids is not None:
            self._set_tags(instance, tag_ids)

        return instance


class RatingSerializer(serializers.ModelSerializer):
    member = MemberSimpleSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ('rating_id', 'score', 'created_at', 'member')


class RatingCreateUpdateSerializer(serializers.Serializer):
    # 단순히 score 값만 받으면 되므로 Serializer 로 충분
    score = serializers.IntegerField(min_value=1, max_value=5)


class RecipeCommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("댓글 내용을 입력해주세요.")
        return value


# ============================
# 인기 레시피 Serializer
# ============================

class PopularRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeSummary
        fields = (
            'recipe_id',
            'title',
            'description',
            'cooking_time',
            'avg_score',
            'rating_count',
            'like_count',
            'comment_count',
        )


# ============================
# 신고(Report) 관련 Serializer
# ============================

class ReportCreateSerializer(serializers.Serializer):
    """
    유저 신고 생성용: reason만 받는다.
    target_type / recipe / comment 는 View에서 세팅
    """
    reason = serializers.CharField()

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("신고 사유를 입력해주세요.")
        return value


class ReportListSerializer(serializers.ModelSerializer):
    """
    관리자용 신고 목록 조회
    """
    reporter = MemberSimpleSerializer(read_only=True)
    handled_by = MemberSimpleSerializer(read_only=True)

    class Meta:
        model = Report
        fields = (
            'report_id',
            'reporter',
            'target_type',
            'recipe_id',
            'comment_id',
            'reason',
            'status',
            'created_at',
            'handled_by',
            'handled_at',
            'handle_note',
        )


class ReportUpdateSerializer(serializers.Serializer):
    """
    관리자 신고 처리용
    """
    status = serializers.ChoiceField(
        choices=['PENDING', 'RESOLVED', 'REJECTED'],
        required=False,
    )
    handle_note = serializers.CharField(required=False, allow_blank=True)

# recipes/serializers.py

from rest_framework import serializers
from .models import Recipe, Ingredient, RecipeIngredient, RecipeStep


class IngredientCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    amount = serializers.CharField(allow_blank=True, required=False)


class StepCreateSerializer(serializers.Serializer):
    step_order = serializers.IntegerField()
    content = serializers.CharField()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True, required=False)
    steps = StepCreateSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'title',
            'description',
            'cooking_time',
            'image_path',  # S3 URL or local path
            'ingredients',
            'steps',
        ]

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients", [])
        steps_data = validated_data.pop("steps", [])

        recipe = Recipe.objects.create(**validated_data)

        # 1) 재료 저장
        for item in ingredients_data:
            ing, _ = Ingredient.objects.get_or_create(name=item["name"])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ing,
                amount=item.get("amount")
            )

        # 2) 단계 저장
        for step in steps_data:
            RecipeStep.objects.create(
                recipe=recipe,
                step_order=step["step_order"],
                content=step["content"]
            )

        return recipe
