import asyncio
import logging
import os
import time

import requests

import aiohttp as aiohttp
import pymongo
from celery import shared_task
from django_celery_results.models import TaskResult

from community.models import Community, Story, Tag, StoryTag, Category, StoryCategory, CommunityChannel, \
    CommunitySetting, Audience, StoryStatusConfig
from community.utils import get_purl, date_format

logger = logging.getLogger('django')

logger.info(f"mongo client url --> {os.environ.get('MONGO_CLIENT_URL')}")
logger.info(f"mongo db name --> {os.environ.get('MONGO_DB_NAME')}")
logger.info(f"mongo collection name --> {os.environ.get('MONGO_COLLECTION_NAME')}")

mongo_client = pymongo.MongoClient(os.environ.get('MONGO_CLIENT_URL'))
logger.info(f"mongo_client --> {mongo_client}")
mongo_db = mongo_client[os.environ.get('MONGO_DB_NAME')]
company_projects_collection = mongo_db[os.environ.get('MONGO_COLLECTION_NAME')]


def sync_function(url, headers, params, update=None, last_story_id=None):
    """
    Function for calling asynchronous function to get all community and stories data.
    """

    data_list = []

    async def async_func():
        page = 1
        status = 200
        repeater_count = 0
        community_page_repeater_count = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            while status == 200:
                full_url = url.format(page=page, per_page=params.get('per_page'),
                                      by_community=params.get('by_community'))
                async with session.get(url=full_url) as resp:
                    try:
                        logger.info(f"CURRENT URL: {full_url}")
                        response_data = await resp.json()
                        status = resp.status
                    except Exception:
                        logger.error(f"URL: {full_url}\nRESPONSE: {await resp.text()}\nSTATUS: {status}")
                        community_page_repeater_count[params.get('by_community')] = {}
                        repeater_count += 1
                        community_page_repeater_count[params.get('by_community')][params.get('page')] = repeater_count
                        if community_page_repeater_count[params.get('by_community')][params.get('page')] == 5:
                            page += 1
                            repeater_count = 0
                            community_page_repeater_count = {}
                        time.sleep(2)
                        continue

                    if status != 200:
                        logger.error(f"URL: {full_url}\nRESPONSE: {await resp.text()}\nSTATUS: {status}")
                        continue
                    if not response_data:
                        return
                    if update:
                        data = []
                        for record in response_data:
                            if record['id'] > last_story_id:
                                data.append(record)
                            else:
                                data_list.extend(data)
                                return data_list
                        data_list.extend(data)
                    else:
                        data_list.extend(response_data)
                    page += 1
                    repeater_count = 0

    asyncio.run(async_func())

    return data_list


def community_story_sync_function(url: str, headers: dict, params: dict, page: int):
    """
    Function for calling asynchronous function to get all community and stories data.
    """

    data_list = []

    async def community_story_async_func(page_n: int):
        page_n += 1
        page_count = 2
        status = 200
        repeater_count = 0
        community_page_repeater_count = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            while status == 200:
                full_url = url.format(page=page_n, per_page=params.get('per_page'),
                                      by_community=params.get('by_community'))
                async with session.get(url=full_url) as resp:
                    try:
                        logger.info(f"CURRENT URL: {full_url}")
                        response_data = await resp.json()
                        status = resp.status
                    except Exception:
                        logger.error(f"URL: {full_url}\nRESPONSE: {await resp.text()}\nSTATUS: {status}")
                        community_page_repeater_count[params.get('by_community')] = {}
                        repeater_count += 1
                        community_page_repeater_count[params.get('by_community')][params.get('page')] = repeater_count
                        if community_page_repeater_count[params.get('by_community')][params.get('page')] == 5:
                            page_n += 1
                            page_count -= 1
                            repeater_count = 0
                            community_page_repeater_count = {}
                        time.sleep(2)
                        continue

                    if status != 200:
                        logger.error(f"URL: {full_url}\nRESPONSE: {await resp.text()}\nSTATUS: {status}")
                        continue
                    if not response_data:
                        # page_n += 1
                        # page_count -= 1
                        return data_list, page_n, True

                    data_list.extend(response_data)
                    page_count -= 1
                    if page_count <= 0:
                        return data_list, page_n, False
                    page_n += 1
                    repeater_count = 0

            return data_list, page_n, False

    data_list, page, is_completed = asyncio.run(community_story_async_func(page))

    return data_list, page, is_completed


def story_community_settings():
    """Function that fetches stories for community settings that are added in the system recursively."""

    try:
        story_url = os.environ.get('STORY_UPDATE_URL')
        community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
        headers = {'Authorization': f'Token {community_data_access_key}'}
        params = {'per_page': 100}

        community_objs = CommunitySetting.objects.filter(
            is_trashed=False).values_list('community__community_id', flat=True)

        if not StoryStatusConfig.objects.filter(is_completed=False).exists():
            return True

        for community_id in community_objs:
            params['by_community'] = community_id

            if not StoryStatusConfig.objects.filter(
                    community__community_id=params.get('by_community')).exists():
                # Adding StoryStatusConfig data for already added community settings.
                community_obj = Community.objects.get(community_id=params.get('by_community'))
                StoryStatusConfig.objects.create(community=community_obj, last_page=0)

            if status_object := StoryStatusConfig.objects.filter(
                    community__community_id=params.get('by_community'),
                    is_trashed=False, is_completed=False
            ).last():
                last_page = status_object.last_page
                logger.info(f"Calling Story ASYNC for Community {community_id} ## Last Page ## {last_page}")

                story_data_list, last_page_called, is_completed = community_story_sync_function(
                    story_url, headers, params, page=last_page)

                logger.info(f"Total Stories in Community: {community_id} is: {len(story_data_list)}")

                community_obj_id = Community.objects.get(community_id=community_id).id
                logger.info(f"Starting Add Stories for Community Id ## {community_obj_id}")

                if story_data_list:
                    add_community_stories(story_data_list, community_obj_id)

                # Updating the status of pages visited from current job.
                status_object.last_page = last_page_called
                status_object.is_completed = is_completed
                status_object.save(update_fields=['last_page', 'is_completed'])

        story_community_settings()

    except Exception as e:
        logger.error(f"story_community_settings error ## {e}")
        return False


@shared_task(name="story_community_settings_main_handler")
def story_community_settings_main_handler():
    """Main story community setting handler that will call story_community_settings()
     which will recursively fetch stories for added community setting."""

    task_list = TaskResult.objects.filter(task_name='story_community_settings_main_handler').exclude(
        task_id=story_community_settings_main_handler.request.id).values_list('status', flat=True)
    if 'STARTED' in task_list or 'PENDING' in task_list:
        logger.info("story_community_settings_main_handler ## TASK ALREADY RUNNING.")
        return

    status = story_community_settings()     # Calling recursive function
    logger.info(f"story_community_settings_main_handler ## COMPLETED with status {status}")

    return True


@shared_task(name="community_data_entry")
def community_data_entry():
    try:
        task_list = TaskResult.objects.filter(task_name='community_data_entry').exclude(
            task_id=community_data_entry.request.id).values_list('status', flat=True)
        if 'STARTED' in task_list or 'PENDING' in task_list:
            logger.info(f"CURRENT TASK ID ## {community_data_entry.request.id}")
            logger.info("## TASK ALREADY RUNNING.")
            return

        community_url = os.environ.get('COMMUNITY_URL')
        community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
        headers = {'Authorization': f'Token {community_data_access_key}'}
        params = {'per_page': 100}
        data = sync_function(url=community_url, headers=headers,
                             params=params)

        try:
            last_community_id = Community.objects.latest('community_id').community_id
        except Exception:
            last_community_id = None

        logger.info(f"last_community_id ## {last_community_id}")

        if last_community_id:
            data = [community for community in data if community.get('id') > last_community_id]

        new_instances = []
        for item in data:
            community_obj = Community(
                community_id=item.get('id'),
                name=item.get('name'),
                client_company_id=item.get('client_company_id'),
                community_metadata=item
            )
            new_instances.append(community_obj)

            if len(new_instances) >= 1000:
                Community.objects.bulk_create(new_instances, ignore_conflicts=True)
                new_instances = []

        if new_instances:
            Community.objects.bulk_create(new_instances, ignore_conflicts=True)

    except Exception as e:
        logger.error(f"community_data_entry error ## {e}")


@shared_task(name="delete_story_data")
def delete_story_data(instance_community_id=None):
    """Job to delete stories whose community setting is either updated or deleted."""

    try:
        Story.objects.filter(community__community_id=instance_community_id).update(is_trashed=True)
        CommunityChannel.objects.filter(community_setting__community__community_id=instance_community_id).update(
            is_trashed=True)
        StoryTag.objects.filter(story__community__community_id=instance_community_id).delete()
        StoryCategory.objects.filter(story__community__community_id=instance_community_id).delete()
        StoryStatusConfig.objects.filter(community__community_id=instance_community_id).update(is_trashed=True)
    except Exception as e:
        logger.error(f"delete_story_data error ## {e}")


@shared_task(name='add_community_stories')
def add_community_stories(story_data_list, community_obj_id):
    """Job to add community stories and related metadata."""

    story_to_be_create_objs = []
    mongo_story_purls = []
    story_tag_category_data = {}

    # ID list of already exists stories.
    story_already_exists_id_list = Story.objects.filter(
        story_id__in=[story.get('id') for story in story_data_list]).values_list('story_id', flat=True)

    # Filtering out not already exists stories.
    story_data_list = [item for item in story_data_list if item.get('id') not in story_already_exists_id_list]

    for story_item in story_data_list:
        tags_list = []
        tags_id_list = []
        for story_tags in story_item.get('story_tags'):
            story_tag_obj = Tag.objects.filter(tag_id=story_tags.get('id')).first()

            if not story_tag_obj:
                story_tag_obj = Tag(tag_id=story_tags.get('id'),
                                    community_id=community_obj_id, title=story_tags.get('name'))
                tags_list.append(story_tag_obj)
            tags_id_list.append(story_tags.get('id'))

        Tag.objects.bulk_create(tags_list, ignore_conflicts=True)   # Bulk creating Tags

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

        Category.objects.bulk_create(categories_list, ignore_conflicts=True)    # Bulk creating Categories

        story_tag_category_data[story_item.get('id')] = {'tags': tags_id_list, 'categories': categories_id_list}

        story_purl = get_purl()
        story_obj = Story(
            story_id=story_item.get('id'),
            title=story_item.get('headline'),
            lede=story_item.get('teaser'),
            community_id=community_obj_id,
            publication_date=date_format(story_item.get('published_at')),
            body=story_item.get('body'),
            p_url=story_purl,
            story_url=story_item.get('story_url'),
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

        if len(story_to_be_create_objs) >= 1000:
            logger.info("## Bulk creating stories")
            Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)
            logger.info("## Bulk creating stories success")
            story_to_be_create_objs = []

    if story_to_be_create_objs:
        logger.info("## Bulk creating stories")
        Story.objects.bulk_create(story_to_be_create_objs, ignore_conflicts=True)
        logger.info("## Bulk creating stories success")

    logger.info("## Adding story tags and categories if any")
    for story in story_tag_category_data:
        # logger.info(f"## tags and categories for story => {story}")
        story = Story.objects.get(story_id=story)

        story.tag.add(*list(Tag.objects.filter(
            tag_id__in=story_tag_category_data.get(story.story_id, {}).get("tags", [])
        ).values_list('id', flat=True)))
        story.category.add(*list(Category.objects.filter(
            category_id__in=story_tag_category_data.get(story.story_id, {}).get("categories", [])
        ).values_list('id', flat=True)))

    if mongo_story_purls:
        company_projects_collection.insert_many(mongo_story_purls)
        logger.info("Added story PURLs.")


def audience_generator(client_id, api_key):
    """Function to call list-audience API and return audiences for community."""

    base_url = os.environ.get("OPNSESAME_API_URL", "")
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }

    logger.info(f"Audiences API Headers ## {headers}")
    logger.info(f"Audiences API URL ## {base_url}{client_id}/audiences")
    resp = requests.request("GET", f"{base_url}{client_id}/audiences", headers=headers)
    next_url = None
    if resp.status_code == 200:
        next_url = resp.json().get("next")
        yield resp.json().get("results")

    while next_url:
        resp = requests.request("GET", f"{next_url}", headers=headers)
        next_url = resp.json().get("next")
        yield resp.json().get("results")

    yield []


def check_already_exists_audience_and_bulk_create(audiences, community_id):
    """Function to check already exists audiences and bulk create audiences"""

    logger.info(f"Bulk creating audiences ## for community -> {community_id}")
    # List of audience_id already exists in the system for this community.
    audience_already_exists_id_list = Audience.objects.filter(
        audience_id__in=[aud.get('id') for aud in audiences],
        community_id=community_id).values_list('audience_id', flat=True)

    # Bulk creating audiences.
    new_audience_instances = [
        Audience(audience_id=aud.get('id'), community_id=community_id, name=aud.get('name'),
                 row_count=aud.get('row_count'), available=aud.get('available'),
                 opted_out=aud.get('opted_out'), non_mobile=aud.get('non_mobile'),
                 routes=aud.get('routes'), created_at=date_format(
                aud.get('created_at')) if aud.get('created_at') else None)
        for aud in audiences if aud.get('id') not in audience_already_exists_id_list]

    Audience.objects.bulk_create(new_audience_instances, ignore_conflicts=True)


@shared_task(name='add_community_audiences')
def add_community_audiences(client_id, api_key, community_id):
    """Function to bulk create audiences fetched from audience generator function."""

    try:
        logger.info("Background task ## add_community_audiences")
        for audiences in audience_generator(client_id=client_id, api_key=api_key):

            check_already_exists_audience_and_bulk_create(audiences=audiences, community_id=community_id)
            logger.info("Bulk creating audiences done.")

    except Exception as err:
        logger.error(f"Error add_community_audiences ## {err}")


def check_newly_added_audiences(audiences, audience_max_id):
    """Function to check newly added audiences and
     return break required flag for further API call."""

    is_break = False
    new_audiences = []

    for aud in audiences:
        if aud.get("id") > audience_max_id:
            new_audiences.append(aud)
        else:
            is_break = True
            break

    return is_break, new_audiences


@shared_task(name='daily_audience_community_updates')
def daily_audience_community_updates():
    """Function to bulk create new audiences fetched from audience generator function."""

    try:
        logger.info("Background task ## add_community_audiences")
        community_channel_objs = CommunityChannel.objects.filter(
            is_trashed=False, channel__name__iexact='opnsesame').values('url', 'api_key',
                                                                        'community_setting__community')

        for community_channel_obj in community_channel_objs:

            try:
                audience_max_id = Audience.objects.filter(
                    community_id=community_channel_obj.get('community_setting__community')
                ).order_by('-id').first().audience_id
            except Exception:
                audience_max_id = 0

            for audiences in audience_generator(client_id=community_channel_obj.get('url'),
                                                api_key=community_channel_obj.get('api_key')):

                # Function call to check newly added audiences.
                is_need_to_break, audiences = check_newly_added_audiences(audiences=audiences,
                                                                          audience_max_id=audience_max_id)

                check_already_exists_audience_and_bulk_create(
                    audiences=audiences, community_id=community_channel_obj.get('community_setting__community'))
                logger.info("Bulk creating audiences done.")

                if is_need_to_break:
                    # No further page check needed.
                    break

    except Exception as err:
        logger.error(f"Error daily_audience_community_updates ## {err}")


@shared_task(name='daily_story_updates')
def daily_story_updates():
    """Function to daily add newly added stories from local labs
     for all community settings added in the system"""

    try:
        story_url = os.environ.get('STORY_UPDATE_URL')
        community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
        headers = {'Authorization': f'Token {community_data_access_key}'}
        params = {'per_page': 100}

        community_objs = CommunitySetting.objects.all().values_list('community__community_id', flat=True)
        for community_id in community_objs:

            if not StoryStatusConfig.objects.filter(
                    community__community_id=community_id, last_page=0).exists():

                try:
                    last_story_id = Story.objects.filter(community__community_id=community_id).latest(
                        'story_id').story_id
                except Exception:
                    last_story_id = 0

                params['by_community'] = community_id
                logger.info(f"Calling Story ASYNC for Community {community_id}")
                story_data_list = sync_function(story_url, headers, params, update=True, last_story_id=last_story_id)
                logger.info(f"Total Stories in Community: {community_id} is: {len(story_data_list)}")

                community_obj_id = Community.objects.get(community_id=community_id).id
                logger.info(f"Starting Add Stories for Community Id ## {community_obj_id}")
                for ind in range(len(story_data_list) // 1000 + 1):
                    story_data_list_store = story_data_list[ind * 1000: 1000 * (ind + 1)]
                    add_community_stories.delay(story_data_list_store, community_obj_id)

    except Exception as e:
        logger.error(f"daily_story_updates error ## {e}")


@shared_task(name='delete_story_with_deleted_community')
def delete_story_with_deleted_community():
    """Function to daily remove stories for all community that are deleted from the system"""

    try:
        community_id_list = CommunitySetting.objects_with_deleted.filter(
            is_trashed=True).values_list('community_id', flat=True).distinct('community_id')
        community_list = [
            community_id
            for community_id in community_id_list
            if not CommunitySetting.objects.filter(
                community_id=community_id
            ).exists()
        ]
        Story.objects.filter(community_id__in=community_list).update(is_trashed=True)
        StoryTag.objects.filter(story__community_id__in=community_list).delete()
        StoryCategory.objects.filter(story__community_id__in=community_list).delete()
        StoryStatusConfig.objects.filter(community_id__in=community_list).update(is_trashed=True)
    except Exception as e:
        logger.error(f"Delete Story with error ## {e}")
