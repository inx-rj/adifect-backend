import django_filters
from django_filters import CharFilter


class StoriesFilter(django_filters.FilterSet):
    from_date = CharFilter(field_name='publication_date', method='filter_from_date')
    to_date = CharFilter(field_name='publication_date', method='filter_to_date')
    title = CharFilter(field_name='title', method='filter_title')
    p_url = CharFilter(field_name='p_url', method='filter_p_url')
    published_at = CharFilter(field_name='story_metadata.published_at', method='filter_published_at')
    updated_at = CharFilter(field_name='story_metadata.updated_at', method='filter_updated_at')
    community = CharFilter(field_name='community.name', method='filter_community')
    tag = CharFilter(field_name='tag.title', method='filter_tag')
    status = CharFilter(field_name='status', method='filter_status')
    ordering = CharFilter(method='filter_ordering')

    def filter_from_date(self, queryset, from_date, value):
        self.queryset = self.queryset.filter(publication_date__gte=value)
        return self.queryset

    def filter_to_date(self, queryset, to_date, value):
        self.queryset = self.queryset.filter(publication_date__lte=value)
        return self.queryset

    def filter_status(self, queryset, status, value):
        self.queryset = self.queryset.filter(status__icontains=value)
        return self.queryset

    def filter_community(self, queryset, community, value):
        self.queryset = self.queryset.filter(community__name__icontains=value)
        return self.queryset

    def filter_tag(self, queryset, tag, value):
        self.queryset = self.queryset.filter(tag__title__icontains=value)
        return self.queryset

    def filter_title(self, queryset, status, value):
        self.queryset = self.queryset.filter(title__icontains=value)
        return self.queryset

    def filter_p_url(self, queryset, status, value):
        self.queryset = self.queryset.filter(p_url__icontains=value)
        return self.queryset

    def filter_published_at(self, queryset, status, value):
        self.queryset = self.queryset.filter(story_metadata__published_at__icontains=value)
        return self.queryset

    def filter_updated_at(self, queryset, status, value):
        self.queryset = self.queryset.filter(story_metadata__updated_at__icontains=value)
        return self.queryset

    def filter_ordering(self, queryset, ordering, value):
        value_list = ['title', 'p_url', 'community__name', 'status', 'tag__title', 'story_metadata__published_at',
                      'story_metadata__updated_at']
        if value in value_list:
            self.queryset = self.queryset.order_by(value)
        return self.queryset
