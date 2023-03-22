from django.db import models

from common.models import BaseModel


class Community(BaseModel):
    community_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    client_company_id = models.IntegerField()
    state = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Community'

    def __str__(self):
        return self.name


class Tag(BaseModel):
    community = models.ForeignKey(Community, related_name='tag_community', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    title = models.CharField(max_length=200)
    is_unique = models.BooleanField(default=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Tag'

    def __str__(self):
        return self.title


class Story(BaseModel):
    title = models.CharField(max_length=200)
    lede = models.TextField()
    image = models.ImageField(upload_to='story_image/', null=True, blank=True)
    word_count = models.IntegerField(default=0)
    community = models.ForeignKey(Community, related_name='story_community', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    publication_date = models.DateField()
    status = models.CharField(max_length=50, null=True, blank=True)
    body = models.TextField()
    p_url = models.CharField(max_length=8, unique=True)
    tag = models.ManyToManyField(Tag, related_name='story_tag', through='StoryTag')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Story'

    def __str__(self):
        return self.title


class StoryTag(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
