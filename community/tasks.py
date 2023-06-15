import asyncio
import logging
import os
import requests

import aiohttp as aiohttp
import pymongo
from celery import shared_task
from django_celery_results.models import TaskResult

from community.models import Community, Story, Tag, StoryTag, Category, StoryCategory, CommunityChannel, Audience
from community.utils import get_purl, date_format

logger = logging.getLogger('django')

logger.info(f"mongo client url --> {os.environ.get('MONGO_CLIENT_URL')}")
logger.info(f"mongo db name --> {os.environ.get('MONGO_DB_NAME')}")
logger.info(f"mongo collection name --> {os.environ.get('MONGO_COLLECTION_NAME')}")

mongo_client = pymongo.MongoClient(os.environ.get('MONGO_CLIENT_URL'))
logger.info(f"mongo_client --> {mongo_client}")
mongo_db = mongo_client[os.environ.get('MONGO_DB_NAME')]
company_projects_collection = mongo_db[os.environ.get('MONGO_COLLECTION_NAME')]


def async_function(url, headers, params):
    page = 1
    status = 200
    repeater_count = 0
    community_page_repeater_count = {}
    data_list = []

    while status == 200:
        full_url = url.format(page=page, per_page=params.get('per_page'),
                              by_community=params.get('by_community'))
        resp = requests.request('GET', url=full_url, headers=headers)
        try:
            print(f"CURRENT URL: {full_url}")
            response_data = resp.json()
            status = resp.status_code
            print(f"response {response_data} || status {status}")
        except Exception:
            print(f"URL: {full_url}\nRESPONSE: {resp.text}\nSTATUS: {status}")
            community_page_repeater_count[params.get('by_community')] = {}
            repeater_count += 1
            community_page_repeater_count[params.get('by_community')][params.get('page')] = repeater_count
            if community_page_repeater_count[params.get('by_community')][params.get('page')] == 5:
                page += 1
                repeater_count = 0
                community_page_repeater_count = {}
            continue
        if status != 200:
            print(f"URL: {full_url}\nRESPONSE: {resp.text}\nSTATUS: {status}")
            continue
        if not response_data:
            return
        data_list.extend(response_data)
        page += 1
        repeater_count = 0

        print("------------------------")
        yield page, status, response_data


def check_for_existing_community_data(new_instances=[]):
    data_already_exists = Community.objects.filter(
        community_id__in=[item.community_id for item in new_instances]).values_list('community_id', flat=True)

    return [item for item in new_instances if item.community_id not in data_already_exists]


def community_data_entry():
    community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
    headers = {'Authorization': f'Token {community_data_access_key}'}
    params = {'per_page': 100}
    url = os.environ.get('COMMUNITY_URL')
    new_instances = []
    for i, j, data in async_function(url=url, headers=headers, params=params):

        for item in data:
            community_obj = Community(
                community_id=item.get('id'),
                name=item.get('name'),
                client_company_id=item.get('client_company_id'),
                community_metadata=item
            )
            new_instances.append(community_obj)

            if len(new_instances) >= 500:
                new_instances = check_for_existing_community_data(new_instances=new_instances)
                Community.objects.bulk_create(new_instances, ignore_conflicts=True)
                new_instances = []

    if new_instances:
        new_instances = check_for_existing_community_data(new_instances=new_instances)
        Community.objects.bulk_create(new_instances, ignore_conflicts=True)


def check_for_existing_story_data(new_instances=[]):
    data_already_exists = Story.objects.filter(
        id__in=[item.get("id") for item in new_instances]).values_list('id', flat=True)

    return [item for item in new_instances if item.get("id") not in data_already_exists]


def check_for_existing_tag_data(community_id, new_instances=[]):
    data_already_exists = Tag.objects.filter(
        tag_id__in=[item.get("id") for item in new_instances]).values_list('tag_id', flat=True)

    return [Tag(tag_id=item.get('id'),
                community_id=community_id,
                title=item.get('name'))
            for item in new_instances if item.get("id") not in data_already_exists]


def check_for_existing_category_data(community_id, new_instances=[]):
    data_already_exists = Category.objects.filter(
        category_id__in=[item.get("id") for item in new_instances]).values_list('category_id', flat=True)

    return [Category(category_id=item.get('id'),
                     community_id=community_id,
                     title=item.get('name'))
            for item in new_instances if item.get("id") not in data_already_exists]


def story_data_entry(community_id, local_community_id):
    community_data_access_key = os.environ.get('COMMUNITY_DATA_ACCESS_KEY')
    headers = {'Authorization': f'Token {community_data_access_key}'}
    params = {'per_page': 100, 'by_community': local_community_id}
    url = os.environ.get('STORY_URL')
    for i, j, data in async_function(url=url, headers=headers, params=params):

        new_instances = []
        mongo_story_purls = []
        story_tag_dict = {}
        story_category_dict = {}

        for story_item in data:
            if story_item.get("community_id") != local_community_id:
                continue

            tags_list = []
            tags_id_list = []
            for story_tags in story_item.get('story_tags'):
                tags_list.append(story_tags)
                tags_id_list.append(story_tags.get("id"))
                tags_list = check_for_existing_tag_data(community_id=community_id, new_instances=tags_list)

            story_tag_dict[story_item.get('id')] = tags_id_list

            Tag.objects.bulk_create(tags_list, ignore_conflicts=True)

            categories_list = []
            categories_id_list = []
            for story_category in story_item.get('story_categories'):
                categories_list.append(story_category)
                categories_id_list.append(story_category.get("id"))
                categories_list = check_for_existing_category_data(community_id=community_id,
                                                                   new_instances=categories_list)

            story_category_dict[story_item.get('id')] = categories_id_list
            Category.objects.bulk_create(categories_list, ignore_conflicts=True)

            story_purl = get_purl()
            story_obj = Story(
                story_id=story_item.get('id'),
                title=story_item.get('headline'),
                lede=story_item.get('teaser'),
                community_id=community_id,
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
            new_instances.append(story_obj)

            if len(new_instances) >= 500:
                logger.info("## Bulk creating stories")
                Story.objects.bulk_create(new_instances, ignore_conflicts=True)
                logger.info("## Bulk creating stories success")
                new_instances = []

        if new_instances:
            logger.info("## Bulk creating stories")
            Story.objects.bulk_create(new_instances, ignore_conflicts=True)
            logger.info("## Bulk creating stories success")

        # story_tag_instances = []
        for story in story_tag_dict:
            story = Story.objects.get(story_id=story)
            story.tag.add(*list(Tag.objects.filter(tag_id__in=story_tag_dict.get(story.story_id, [])
                                                   ).values_list('id', flat=True)))

        # story_category_instances = []
        for story in story_category_dict:
            story = Story.objects.get(story_id=story)
            story.category.add(*list(Category.objects.filter(category_id__in=story_category_dict.get(story.story_id, [])
                                                             ).values_list('id', flat=True)))

        # if mongo_story_purls:
        #     company_projects_collection.insert_many(mongo_story_purls)
        #     logger.info("Added story PURLs.")


@shared_task(name="community_data_entry")
def sync_community_task_main():
    asyncio.run(community_data_entry())


@shared_task(name="add_community_stories")
def sync_story_task_main(community_id, local_community_id):
    story_data_entry(community_id=community_id, local_community_id=local_community_id)


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
        resp = requests.request("GET", f"{base_url}{client_id}/audiences", headers=headers)
        next_url = resp.json().get("next")
        yield resp.json().get("results")

    yield []


@shared_task(name='add_community_audiences')
def add_community_audiences(client_id, api_key, community_id):
    """Function to bulk create audiences fetched from audience generator function."""

    try:
        logger.info("Background task ## add_community_audiences")
        for audiences in audience_generator(client_id=client_id, api_key=api_key):
            logger.info(f"Bulk creating audiences ## Length of audiences -> {len(audiences)}")
            new_audience_instances = [
                Audience(audience_id=aud.get('id'), community_id=community_id, name=aud.get('name'),
                         row_count=aud.get('row_count'), available=aud.get('available'),
                         opted_out=aud.get('opted_out'), non_mobile=aud.get('non_mobile'),
                         routes=aud.get('routes'), created_at=date_format(
                        aud.get('created_at')) if aud.get('created_at') else None)
                for aud in audiences]
            Audience.objects.bulk_create(new_audience_instances, ignore_conflicts=True)
            logger.info("Bulk creating audiences done.")

    except Exception as err:
        logger.error(f"Error add_community_audiences ## {err}")
