from django.contrib import admin

from publication.models import Publication, Article, Tag, ArticleTag

# Register your models here.
admin.site.register(Publication)
admin.site.register(Tag)
admin.site.register(ArticleTag)


class ArticleTagAdmin(admin.TabularInline):
    model = ArticleTag
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'lede', 'word_count', 'publication', 'publication_date', 'status', 'body', 'p_url', 'is_active')
    inlines = (ArticleTagAdmin, )


