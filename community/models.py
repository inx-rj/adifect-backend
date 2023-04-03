from django.db import models

from common.models import BaseModel


class Community(BaseModel):
    community_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=50)
    client_company_id = models.IntegerField()
    state = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    community_metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Community'

    def __str__(self):
        return self.name


class Tag(BaseModel):
    tag_id = models.IntegerField(null=True, blank=True)
    community = models.ForeignKey(Community, related_name='tag_community', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    title = models.TextField()
    is_unique = models.BooleanField(default=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Tag'
        unique_together = ('community', 'title')

    def __str__(self):
        return self.title


class Category(BaseModel):
    category_id = models.IntegerField(null=True, blank=True)
    community = models.ForeignKey(Community, related_name='category_community', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    title = models.TextField()
    is_unique = models.BooleanField(default=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Category'
        unique_together = ('community', 'title')

    def __str__(self):
        return self.title


class Story(BaseModel):
    story_id = models.IntegerField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    lede = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    word_count = models.IntegerField(default=0)
    community = models.ForeignKey(Community, related_name='story_community', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    publication_date = models.DateField()
    status = models.CharField(max_length=50, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    p_url = models.CharField(max_length=8, unique=True)
    tag = models.ManyToManyField(Tag, related_name='story_tag', through='StoryTag')
    category = models.ManyToManyField(Category, related_name='story_category', through='StoryCategory')
    analytic = models.ManyToManyField(Tag, related_name='story_analytic', through='StoryTagAnalytic')
    is_active = models.BooleanField(default=True)
    story_metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Story'

    def __str__(self):
        return self.title


class StoryTag(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class StoryCategory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class StoryTagAnalytic(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
