import django_filters
from django_filters import CharFilter


class StoriesFilter(django_filters.FilterSet):

    from_date = CharFilter(field_name='publication_date', method='filter_from_date')
    to_date = CharFilter(field_name='publication_date', method='filter_to_date')
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

    def filter_ordering(self, queryset, ordering, value):
        value_list = ['title', 'p_url', 'community__name', 'status', 'tags__title']
        if value in value_list:
            self.queryset = self.queryset.order_by(value)
        return self.queryset
