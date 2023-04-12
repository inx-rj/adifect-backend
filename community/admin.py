from django.contrib import admin

from community.models import Community, Story, Tag, StoryTag, Channel, CommunityChannel

# Register your models here.
admin.site.register(Community)
admin.site.register(Tag)
admin.site.register(StoryTag)
admin.site.register(Channel)
admin.site.register(CommunityChannel)


class ArticleTagAdmin(admin.TabularInline):
    model = StoryTag
    extra = 1


@admin.register(Story)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'lede', 'word_count', 'community', 'publication_date', 'status', 'body', 'p_url', 'is_active')
    inlines = (ArticleTagAdmin,)
