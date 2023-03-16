from django.db import models

from authentication.manager import SoftDeleteManager
from common.models import BaseModel


class Publication(BaseModel):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Tag(BaseModel):
    publication = models.ForeignKey(Publication, related_name='tag_publication', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    title = models.TextField()
    is_unique = models.BooleanField(default=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Article(BaseModel):
    title = models.TextField()
    lede = models.TextField()
    image = models.ImageField()
    word_count = models.IntegerField(default=0)
    publication = models.ForeignKey(Publication, related_name='article_publication', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    publication_data = models.DateField()
    status = models.BooleanField()
    body = models.TextField()
    p_url = models.URLField()
    tag = models.ManyToManyField(Tag, related_name='article_tag')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    is_trashed = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_trashed = True
        self.save()

    def restore(self):
        self.is_trashed = False
        self.save()

    class Meta:
        abstract = True


