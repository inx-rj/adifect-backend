import asyncio
import os
import time

import aiohttp as aiohttp
import requests
from celery import shared_task

from community.models import Community, Story, Tag, StoryTag, Category
from community.utils import get_purl, date_format


# @shared_task(name="community_data_entry")
# def community_data_entry():
#     """
#     Community data is fetched from the production url, and then it is being loaded into the database
#     """
#     url = os.environ.get('community_url')
#     community_data_access_key = os.environ.get('community_data_access_key')
#     headers = {'Authorization': f'Token {community_data_access_key}'}
#     params = {'per_page': 1}
#     response = requests.get(url, headers=headers, params=params)
#
#     if response.status_code == 200:
#         data = response.json()
#         try:
#             last_community_id = Community.objects.latest('community_id').community_id
#         except Community.DoesNotExist:
#             last_community_id = None
#
#         if last_community_id:
#             data = [community for community in data if community.get('id') > last_community_id]
#
#         new_instances = []
#         lst_community_id = []
#         for item in data:
#             lst_community_id.append(item.get('id'))
#             community_obj = Community(
#                 community_id=item.get('id'),
#                 name=item.get('name'),
#                 client_company_id=item.get('client_company_id'),
#                 community_metadata=item
#             )
#             new_instances.append(community_obj)
#
#         if new_instances:
#             Community.objects.bulk_create(new_instances, ignore_conflicts=True)
#
#         for community_id in lst_community_id:
#             page_num = 1
#             story_id_instances = []
#             while True:
#                 url = os.environ.get('story_url')
#                 community_data_access_key = os.environ.get('community_data_access_key')
#                 headers = {'Authorization': f'Token {community_data_access_key}'}
#                 params = {'per_page': 100, 'by_community': community_id, 'page': page_num}
#                 response = requests.get(url, headers=headers, params=params)
#                 story_data = response.json()
#                 if not story_data:
#                     break
#
#                 story_tag_dict = {}
#                 for story_item in story_data:
#                     community_obj = Community.objects.get(community_id=story_item.get('community_id'))
#
#                     tags_list = []
#                     tags_id_list = []
#                     for story_tags in story_item.get('story_tags'):
#                         story_tag_obj = Tag.objects.filter(tag_id=story_tags.get('id')).first()
#
#                         if not story_tag_obj:
#                             story_tag_obj = Tag(tag_id=story_tags.get('id'), community=community_obj, title=story_tags.get('name'), description=story_tags.get('name'))
#                             tags_list.append(story_tag_obj)
#                         tags_id_list.append(story_tags.get('id'))
#                     story_tag_dict[story_item.get('id')] = tags_id_list
#                     Tag.objects.bulk_create(tags_list, ignore_conflicts=True)
#
#                     story_obj = Story(
#                         story_id=story_item.get('id'),
#                         title=story_item.get('headline'),
#                         lede=story_item.get('teaser'),
#                         community=community_obj,
#                         image=story_item.get('images')[0] if story_item.get('images') else None,
#                         publication_date=date_format(story_item.get('published_at')),
#                         body=story_item.get('body'),
#                         p_url=get_purl(),
#                         story_metadata=story_item
#                     )
#                     if story_item.get('published') and not story_item.get('scheduled'):
#                         story_obj.status = 'Published'
#                     if not story_item.get('published') and not story_item.get('scheduled'):
#                         story_obj.status = 'Draft'
#                     if not story_item.get('published') and story_item.get('scheduled'):
#                         story_obj.status = 'Scheduled'
#                     story_id_instances.append(story_obj)
#                 Story.objects.bulk_create(story_id_instances, ignore_conflicts=True)
#
#                 story_tag_instances = []
#
#                 for story in story_tag_dict:
#                     story_id = Story.objects.get(story_id=story).id
#                     for tag in story_tag_dict.get(story, []):
#                         tag_id = Tag.objects.get(tag_id=tag).id
#                         story_tag_instances.append(StoryTag(
#                             story_id=story_id,
#                             tag_id=tag_id
#                         ))
#
#                 StoryTag.objects.bulk_create(story_tag_instances, ignore_conflicts=True)
#                 page_num += 1


def sync_function(url, community_data_access_key, headers, params):
    story_data_list = []

    async def async_func():
        page = 1
        async with aiohttp.ClientSession(headers=headers) as session:

            while True:
                async with session.get(url=url.format(page=page, per_page=params.get('per_page'),
                                                      by_community=params.get('by_community'))) as resp:

                    print(url.format(page=page, per_page=params.get('per_page'),
                                     by_community=params.get('by_community')))
                    story_data = await resp.json()
                    print(len(story_data))
                    if not story_data:
                        return
                    story_data_list.extend(story_data)
                    page += 1

    asyncio.run(async_func())

    return story_data_list


def community_sync_function(url, community_data_access_key, headers, params):
    story_data_list = []

    async def community_async_func():
        page = 1
        async with aiohttp.ClientSession(headers=headers) as session:

            while True:
                async with session.get(url=url.format(page=page, per_page=params.get('per_page'),
                                                      by_community=params.get('by_community'))) as resp:

                    print(url.format(page=page, per_page=params.get('per_page'),
                                     by_community=params.get('by_community')))
                    story_data = await resp.json()
                    print(len(story_data))
                    if not story_data:
                        return
                    story_data_list.extend(story_data)
                    page += 1

    asyncio.run(community_async_func())

    return story_data_list


@shared_task(name="community_data_entry")
def community_data_entry():
    """
    Community data is fetched from the production url, and then it is being loaded into the database
    """
    print("community_data_entry---")
    start_time = time.time()
    url = os.environ.get('community_url')
    story_url = os.environ.get('story_url')
    community_data_access_key = os.environ.get('community_data_access_key')
    headers = {'Authorization': f'Token {community_data_access_key}'}
    params = {'per_page': 100}
    data = community_sync_function(url=url, community_data_access_key=community_data_access_key, headers=headers,
                                   params=params)

    try:
        last_community_id = Community.objects.latest('community_id').community_id
    except Community.DoesNotExist:
        last_community_id = None

    if last_community_id:
        data = [community for community in data if community.get('id') > last_community_id]

    new_instances = []
    # lst_community_id = []
    for item in data:
        # lst_community_id.append(item.get('id'))

        community_obj = Community(
            community_id=item.get('id'),
            name=item.get('name'),
            client_company_id=item.get('client_company_id'),
            community_metadata=item
        )
        new_instances.append(community_obj)

        if len(new_instances) >= 5000:
            Community.objects.bulk_create(new_instances, ignore_conflicts=True)
            new_instances = []

    if new_instances:
        Community.objects.bulk_create(new_instances, ignore_conflicts=True)

    for community_id in data:

        params['by_community'] = community_id.get('id')
        print(f"Calling Story ASYNC for Community {community_id.get('id')}")
        story_data_list = sync_function(story_url, community_data_access_key, headers, params)
        print(f"Total Stories in Community: {community_id.get('id')} is: {len(story_data_list)}")

        max_story_id = max(Story.objects.filter().values_list('story_id'))
        story_data_list = [story for story in story_data_list if story.get('id') > max_story_id]

        story_to_be_create_objs = []
        story_tag_dict = {}
        story_category_dict = {}
        community_obj = Community.objects.get(community_id=community_id.get('id'))
        for story_item in story_data_list:

            if story_item.get('community_id') != community_id.get('id'):
                # Skip if the community_id is different
                continue

            tags_list = []
            tags_id_list = []
            for story_tags in story_item.get('story_tags'):
                story_tag_obj = Tag.objects.filter(tag_id=story_tags.get('id')).first()

                if not story_tag_obj:
                    story_tag_obj = Tag(tag_id=story_tags.get('id'),
                                        community=community_obj, title=story_tags.get('name'),
                                        description=story_tags.get('name'))
                    tags_list.append(story_tag_obj)
                tags_id_list.append(story_tags.get('id'))
            story_tag_dict[story_item.get('id')] = tags_id_list

            Tag.objects.bulk_create(tags_list, ignore_conflicts=True)

            # Story Category

            categories_list = []
            categories_id_list = []
            for story_category in story_item.get('story_categories'):
                story_category_obj = Category.objects.filter(category_id=story_category.get('id')).first()

                if not story_category_obj:
                    story_category_obj = Tag(category_id=story_category.get('id'),
                                             community=community_obj, title=story_category.get('name'),
                                             description=story_category.get('name'))
                    categories_list.append(story_category_obj)
                categories_id_list.append(story_category.get('id'))
            story_category_dict[story_item.get('id')] = categories_id_list

            Category.objects.bulk_create(categories_list, ignore_conflicts=True)

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
            story_to_be_create_objs.append(story_obj)

            if len(story_to_be_create_objs) >= 5000:
                Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)
                story_to_be_create_objs = []

        if story_to_be_create_objs:
            Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)

        story_tag_instances = []

        for story in story_tag_dict:
            story_id = Story.objects.get(story_id=story).id
            for tag in story_tag_dict.get(story, []):
                tag_id = Tag.objects.get(tag_id=tag).id
                story_tag_instances.append(StoryTag(
                    story_id=story_id,
                    tag_id=tag_id
                ))

        StoryTag.objects.bulk_create(story_tag_instances, ignore_conflicts=True)

    print(f"TIME: {time.time() - start_time}")
