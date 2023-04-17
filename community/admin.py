from django.contrib import admin

from community.models import Community, Story, Tag, StoryTag, Channel, CommunityChannel, CommunitySetting

# Register your models here.
admin.site.register(Community)
admin.site.register(Tag)
admin.site.register(StoryTag)
admin.site.register(Channel)
admin.site.register(CommunityChannel)


class StoryTagAdmin(admin.TabularInline):
    model = StoryTag
    extra = 1


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'lede', 'word_count', 'community', 'publication_date', 'status', 'body', 'p_url', 'is_active')
    inlines = (StoryTagAdmin,)


class CommunityChannelAdmin(admin.TabularInline):
    model = CommunityChannel
    extra = 1


@admin.register(CommunitySetting)
class CommunitySettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'community', 'is_active')
    inlines = (CommunityChannelAdmin,)
