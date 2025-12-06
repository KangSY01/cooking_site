from django.db import models


class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    login_id = models.CharField(unique=True, max_length=50)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=50)
    role = models.TextField()  # PostgreSQL enum(user_role) 매핑 추정
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'member'


class Follow(models.Model):
    follower = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='following_set',
    )
    followee = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='follower_set',
    )
    followed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'follow'
        # DB에서는 복합 PK/UNIQUE 제약일 가능성 높음
        # Django 쪽에서도 무결성 표현
        unique_together = ('follower', 'followee')


class Ingredient(models.Model):
    ingredient_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'ingredient'


class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'tag'


class Recipe(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    author = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='recipes',
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    cooking_time = models.IntegerField(blank=True, null=True)
    image_path = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    avg_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
    )
    rating_count = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe'


class RecipeStep(models.Model):
    step_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='steps',
    )
    step_order = models.IntegerField()
    content = models.TextField()

    class Meta:
        managed = False
        db_table = 'recipe_step'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        models.DO_NOTHING,
        related_name='ingredient_recipes',
    )
    amount = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_ingredient'
        unique_together = ('recipe', 'ingredient')


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='recipe_tags',
        primary_key=True,
    )
    tag = models.ForeignKey(
        Tag,
        models.DO_NOTHING,
        related_name='tag_recipes',
    )

    class Meta:
        managed = False
        db_table = 'recipe_tag'
        unique_together = ('recipe', 'tag')


class RecipeLike(models.Model):
    member = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='recipe_likes',
    )
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='likes',
    )
    liked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_like'
        unique_together = ('member', 'recipe')


class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='ratings',
    )
    member = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='ratings',
    )
    score = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rating'
        unique_together = ('recipe', 'member')


class RecipeComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        related_name='comments',
    )
    author = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='comments',
    )
    parent_comment = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='replies',
    )
    content = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_comment'


class Report(models.Model):
    report_id = models.AutoField(primary_key=True)
    reporter = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='reports',
    )
    target_type = models.TextField()  # recipe / comment 등 enum(string)으로 저장 추정
    recipe = models.ForeignKey(
        Recipe,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='reports',
    )
    comment = models.ForeignKey(
        RecipeComment,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='reports',
    )
    reason = models.TextField()
    status = models.TextField(blank=True, null=True)  # pending / approved / rejected 등
    created_at = models.DateTimeField(blank=True, null=True)
    handled_by = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        db_column='handled_by',
        related_name='handled_reports',
        blank=True,
        null=True,
    )
    handled_at = models.DateTimeField(blank=True, null=True)
    handle_note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'report'


class UserSanction(models.Model):
    sanction_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        related_name='sanctions',
    )
    sanction = models.TextField()  # warning / suspension 등 enum(string) 추정
    reason = models.TextField()
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        Member,
        models.DO_NOTHING,
        db_column='created_by',
        related_name='created_sanctions',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_sanction'