from django.contrib import admin

from publication.models import Publication, Article, Tag, ArticleTag

# Register your models here.
admin.site.register(Publication)
admin.site.register(Article)
admin.site.register(Tag)
admin.site.register(ArticleTag)
