import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import aiohttp as aiohttp
import pymongo
from celery import shared_task
from django_celery_results.models import TaskResult

from community.models import Community, Story, Tag, StoryTag, Category, StoryCategory
from community.utils import get_purl, date_format

logger = logging.getLogger('django')

logger.info(f"mongo client url --> {os.environ.get('MONGO_CLIENT_URL')}")
logger.info(f"mongo db name --> {os.environ.get('MONGO_DB_NAME')}")
logger.info(f"mongo collection name --> {os.environ.get('MONGO_COLLECTION_NAME')}")

mongo_client = pymongo.MongoClient(os.environ.get('MONGO_CLIENT_URL'))
logger.info(f"mongo_client --> {mongo_client}")
mongo_db = mongo_client[os.environ.get('MONGO_DB_NAME')]
company_projects_collection = mongo_db[os.environ.get('MONGO_COLLECTION_NAME')]


def sync_function(url, headers, params):
    """
    Function for calling asynchronous function to get all community and stories data.
    """

    data_list = []

    async def async_func():
        page = 1
        status = 200
        async with aiohttp.ClientSession(headers=headers) as session:
            while status == 200:
                full_url = url.format(page=page, per_page=params.get('per_page'),
                                      by_community=params.get('by_community'))
                async with session.get(url=full_url) as resp:

                    response_data = await resp.json()
                    status = resp.status
                    if status != 200:
                        logger.error(f"URL: {full_url}\nRESPONSE: {await resp.text()}\nSTATUS: {status}")
                        continue
                    if not response_data:
                        return
                    data_list.extend(response_data)
                    page += 1

    asyncio.run(async_func())

    return data_list


def store_data(story_data_list, community_id):
    community_obj_id = Community.objects.get(community_id=community_id.get('id')).id
    logger.info(f"Starting Add Stories for Community Id ## {community_obj_id}")

    story_to_be_create_objs = []
    mongo_story_purls = []
    story_tag_dict = {}
    story_category_dict = {}

    for story_item in story_data_list:

        tags_list = []
        tags_id_list = []
        for story_tags in story_item.get('story_tags'):
            story_tag_obj = Tag.objects.filter(tag_id=story_tags.get('id')).first()

            if not story_tag_obj:
                story_tag_obj = Tag(tag_id=story_tags.get('id'),
                                    community_id=community_obj_id, title=story_tags.get('name'),
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
                story_category_obj = Category(category_id=story_category.get('id'),
                                              community_id=community_obj_id, title=story_category.get('name'),
                                              description=story_category.get('name'))
                categories_list.append(story_category_obj)
            categories_id_list.append(story_category.get('id'))
        story_category_dict[story_item.get('id')] = categories_id_list

        Category.objects.bulk_create(categories_list, ignore_conflicts=True)

        story_purl = get_purl()
        story_obj = Story(
            story_id=story_item.get('id'),
            title=story_item.get('headline'),
            lede=story_item.get('teaser'),
            community_id=community_obj_id,
            publication_date=date_format(story_item.get('published_at')),
            body=story_item.get('body'),
            p_url=story_purl,
            story_metadata=story_item
        )
        story_obj.set_image(story_item.get("images")) if story_item.get("images") else None
        mongo_story_purls.append({'base_purl': story_purl, "medium": "", "url": ""})

        if story_item.get('published') and not story_item.get('scheduled'):
            story_obj.status = 'Published'
        if not story_item.get('published') and not story_item.get('scheduled'):
            story_obj.status = 'Draft'
        if not story_item.get('published') and story_item.get('scheduled'):
            story_obj.status = 'Scheduled'
        story_to_be_create_objs.append(story_obj)

        if len(story_to_be_create_objs) >= 5000:
            logger.info("## Bulk creating stories")
            Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)
            logger.info("## Bulk creating stories success")
            story_to_be_create_objs = []

    if story_to_be_create_objs:
        logger.info("## Bulk creating stories")
        Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)
        logger.info("## Bulk creating stories success")

    story_tag_instances = []
    for story in story_tag_dict:
        story_id = Story.objects.get(story_id=story).id
        for tag in story_tag_dict.get(story, []):
            tag_id = Tag.objects.get(tag_id=tag).id
            story_tag_instances.append(StoryTag(
                story_id=story_id,
                tag_id=tag_id
            ))

            if len(story_tag_instances) >= 5000:
                StoryTag.objects.bulk_create(story_tag_instances, ignore_conflicts=True)
                story_tag_instances = []

    if story_tag_instances:
        StoryTag.objects.bulk_create(story_tag_instances, ignore_conflicts=True)

    story_category_instances = []
    for story in story_category_dict:
        story_id = Story.objects.get(story_id=story).id
        for category in story_category_dict.get(story, []):
            category_id = Category.objects.get(category_id=category).id
            story_category_instances.append(StoryCategory(
                story_id=story_id,
                category_id=category_id
            ))

            if len(story_category_instances) >= 5000:
                StoryCategory.objects.bulk_create(story_category_instances, ignore_conflicts=True)
                story_category_instances = []

    if story_category_instances:
        StoryCategory.objects.bulk_create(story_category_instances, ignore_conflicts=True)
    if mongo_story_purls:
        company_projects_collection.insert_many(mongo_story_purls)
        logger.info("Added story PURLs.")


@shared_task(name="community_data_entry")
def community_data_entry():
    """
    Community data is fetched from the production url, and then it is being loaded into the database
    """

    try:
        task_list = TaskResult.objects.filter(task_name='community_data_entry').exclude(
            task_id=community_data_entry.request.id).values_list('status', flat=True)
        if 'STARTED' in task_list or 'PENDING' in task_list:
            logger.info(f"CURRENT TASK ID ## {community_data_entry.request.id}")
            logger.info("## TASK ALREADY RUNNING.")
            return

        start_time = time.time()
        community_url = os.environ.get('COMMUNITY_URL')
        story_url = os.environ.get('STORY_URL')
        community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
        headers = {'Authorization': f'Token {community_data_access_key}'}
        params = {'per_page': 100}
        data = sync_function(url=community_url, headers=headers,
                             params=params)

        try:
            last_community_id = Community.objects.latest('community_id').community_id
        except Community.DoesNotExist:
            last_community_id = None

        logger.info(f"last_community_id ## {last_community_id}")

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

        with ThreadPoolExecutor(max_workers=10) as executor:

            for community_id in data:

                params['by_community'] = community_id.get('id')
                logger.info(f"Calling Story ASYNC for Community {community_id.get('id')}")
                story_data_list = sync_function(story_url, headers, params)
                logger.info(f"Total Stories in Community: {community_id.get('id')} is: {len(story_data_list)}")

                try:
                    max_story_id = Story.objects.filter(community_id=community_id.get('id')).latest('story_id').story_id
                except Story.DoesNotExist:
                    max_story_id = 0

                story_data_list = [story for story in story_data_list if story.get('id') > max_story_id and story.get(
                    'community_id') == community_id.get('id')]

                story_data_lists = [story_data_list[i:i + 1000] for i in range(0, len(story_data_list), 1000)]

                futures = []
                for story_data_list in story_data_lists:
                    futures.append(executor.submit(store_data, story_data_list, community_id))

                # wait for all tasks to complete
                for future in futures:
                    future.result()

        logger.info(f"ALL DATA ADDED IN TIME: {time.time() - start_time}")
    except Exception as e:
        logger.error(f"community_data_entry error ## {e}")
