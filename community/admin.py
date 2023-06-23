from django.contrib import admin

from community.models import Community, Story, Tag, Category, StoryTag, StoryCategory, Channel, CommunityChannel, \
    CommunitySetting, Program, CopyCode, CreativeCode, Audience

# Register your models here.
admin.site.register(StoryTag)
admin.site.register(StoryCategory)
admin.site.register(CommunityChannel)
admin.site.register(Program)
admin.site.register(CopyCode)
admin.site.register(CreativeCode)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """
    Customizing admin view of Community Table
    """
    list_display = ('id', 'community_id', 'name', 'is_active')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Customizing admin view of Tag Table
    """
    list_display = ('id', 'tag_id', 'title', 'is_active')


@admin.register(Channel)
class TagAdmin(admin.ModelAdmin):
    """
    Customizing admin view of Channel Table
    """
    list_display = ('id', 'name', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customizing admin view of Category Table
    """
    list_display = ('id', 'category_id', 'title', 'is_active')


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


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'community', 'opted_out', 'available')
