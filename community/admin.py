from django.contrib import admin

from community.models import Community, Story, Tag, Category, StoryTag, StoryCategory, Channel, CommunityChannel, \
    CommunitySetting, Program

# Register your models here.
admin.site.register(Community)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(StoryTag)
admin.site.register(StoryCategory)
admin.site.register(Channel)
admin.site.register(CommunityChannel)
admin.site.register(Program)


class StoryTagAdmin(admin.TabularInline):
    model = StoryTag
    extra = 1


class StoryCategoryAdmin(admin.TabularInline):
    model = StoryCategory
    extra = 1


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'lede', 'word_count', 'community', 'publication_date', 'status', 'body', 'p_url', 'is_active')
    inlines = (StoryTagAdmin, StoryCategoryAdmin)


class CommunityChannelAdmin(admin.TabularInline):
    model = CommunityChannel
    extra = 1


@admin.register(CommunitySetting)
class CommunitySettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'community', 'is_active')
    inlines = (CommunityChannelAdmin,)
