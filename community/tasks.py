import os

import requests
from celery import shared_task

from community.models import Community, Story, Tag, StoryTag
from community.utils import get_purl, date_format


@shared_task(name="community_data_entry")
def community_data_entry():
    """
    Community data is fetched from the production url, and then it is being loaded into the database
    """
    url = os.environ.get('community_url')
    community_data_access_key = os.environ.get('community_data_access_key')
    headers = {'Authorization': f'Token {community_data_access_key}'}
    params = {'per_page': 1}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        try:
            last_community_id = Community.objects.latest('community_id').community_id
        except Community.DoesNotExist:
            last_community_id = None

        if last_community_id:
            data = [community for community in data if community.get('id') > last_community_id]

        new_instances = []
        lst_community_id = []
        for item in data:
            lst_community_id.append(item.get('id'))
            community_obj = Community(
                community_id=item.get('id'),
                name=item.get('name'),
                client_company_id=item.get('client_company_id'),
                community_metadata=item
            )
            new_instances.append(community_obj)

        if new_instances:
            Community.objects.bulk_create(new_instances, ignore_conflicts=True)

        for community_id in lst_community_id:
            # print(1)
            page_num = 1
            story_id_instances = []
            story_tag_instances = []
            while True:
                # print(2)
                url = os.environ.get('story_url')
                community_data_access_key = os.environ.get('community_data_access_key')
                headers = {'Authorization': f'Token {community_data_access_key}'}
                params = {'per_page': 100, 'by_community': community_id, 'page': page_num}
                response = requests.get(url, headers=headers, params=params)
                story_data = response.json()
                if not story_data:
                    break

                for story_item in story_data:
                    community_obj = Community.objects.get(community_id=story_item.get('community_id'))

                    # if story_item.get('story_tags'):
                    tags_list = []
                    for story_tags in story_item.get('story_tags'):
                        story_tag_obj = Tag.objects.filter(tag_id=story_tags.get('id')).first()
                        if not story_tag_obj:
                            story_tag_obj = Tag(tag_id=story_tags.get('id'), community=community_obj, title=story_tags.get('name'), description=story_tags.get('title'))
                            tags_list.append(story_tag_obj)
                    Tag.objects.bulk_create(tags_list, ignore_conflicts=True)
                    # print(3)
                    story_tags_list = [obj.get('id') for obj in story_item.get('story_tags')]
                    queryset_story_tags_list = Tag.objects.filter(tag_id__in=story_tags_list).values_list('id')
                    story_obj = Story(
                        story_id=story_item.get('id'),
                        title=story_item.get('headline'),
                        lede=story_item.get('teaser'),
                        community=community_obj,
                        image=story_item.get('images')[0] if story_item.get('images') else None,
                        publication_date=date_format(story_item.get('published_at')),
                        body=story_item.get('body'),
                        p_url=get_purl(),
                        story_metadata=story_item
                    )
                    if story_item.get('published') and not story_item.get('scheduled'):
                        story_obj.status = 'Published'
                    if not story_item.get('published') and not story_item.get('scheduled'):
                        story_obj.status = 'Draft'
                    if not story_item.get('published') and story_item.get('scheduled'):
                        story_obj.status = 'Scheduled'
                    # story_obj.tag.set(queryset_story_tags_list)
                    story_id_instances.append(story_obj)
                    story_tag_instances = [StoryTag(
                        story=story_obj,
                        tag_id=obj_id
                    ) for obj_id in queryset_story_tags_list]
                Story.objects.bulk_create(story_id_instances, ignore_conflicts=True)
                StoryTag.objects.bulk_create(story_tag_instances, ignore_conflicts=True)
                # print(4)
                page_num += 1
