from django.db import models

from common.models import BaseModel


class Publication(BaseModel):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Tag(BaseModel):
    publication = models.ForeignKey(Publication, related_name='tag_publication', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    title = models.CharField(max_length=200)
    is_unique = models.BooleanField(default=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Article(BaseModel):
    title = models.CharField(max_length=200)
    lede = models.TextField()
    image = models.ImageField(upload_to='article_image/', null=True, blank=True)
    word_count = models.IntegerField(default=0)
    publication = models.ForeignKey(Publication, related_name='article_publication', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    publication_date = models.DateField()
    status = models.BooleanField()
    body = models.TextField()
    p_url = models.CharField(max_length=8, unique=True)
    tag = models.ManyToManyField(Tag, related_name='article_tag', through='ArticleTag')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
