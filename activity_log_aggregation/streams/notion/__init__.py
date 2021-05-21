import arrow
import requests
from enum import Enum
from typing import List, Optional

from activity_log_aggregation import utils
from activity_log_aggregation.utils import env
from notion.client import NotionClient
from activity_log_aggregation.streams.stream_event import StreamEvent, StreamVendorName

client = NotionClient(token_v2=env.NOTION_TOKEN_V2)
client.set_user_by_email(env.NOTION_EMAIL)

NOTION_BASE_URL = "https://www.notion.so"
MAX_ITEMS_TO_FETCH = 100  # NOTE: useful for an initial fetch


class _ActivityType(Enum):
    Deleted = "Deleted"
    Edited = "Edited"
    Created = "Created"


def _get_user_id(record_map: dict) -> Optional[str]:
    for key, relevant_user in record_map["notion_user"].items():
        if relevant_user["value"]["email"] == env.NOTION_EMAIL:
            return key


def _convert_activity_type(notion_activity_type: str) -> _ActivityType:
    if "deleted" in notion_activity_type:
        return _ActivityType.Deleted
    elif "edited" in notion_activity_type:
        return _ActivityType.Edited
    elif "created" in notion_activity_type:
        return _ActivityType.Created


def _find_possible_context_id(record_map: dict, activity: dict) -> Optional[str]:
    collection_id = activity.get("collection_id")
    for k, v in record_map.get("collection", {}).items():
        if collection_id == k:
            # maybe check if type is "page" and/or parent_table is "collection"?
            return v["value"]["parent_id"]


def _construct_notion_url(record_map: dict, activity: dict) -> str:
    parent_id = activity["parent_id"]
    urlize_id = lambda id: id.replace('-', '')
    context_id = _find_possible_context_id(record_map, activity)
    is_block = activity.get("parent_table") == "block"
    return f"{NOTION_BASE_URL}/{urlize_id(context_id)}?p={urlize_id(parent_id)}" if context_id and is_block \
        else f"{NOTION_BASE_URL}/{urlize_id(parent_id)}"


def _activity_is_user(record_map: dict, activity: dict) -> bool:
    user_id = _get_user_id(record_map)
    edits = activity.get("edits", [])
    authors = []
    for e in edits:
        authors.extend(e["authors"])
    return next(a["id"] == user_id for a in authors) is not None


def _make_description_of_activity(activity: dict) -> str:
    items = utils.get_recursively(activity, "title")
    try:
        item = items[0][0][0]
        return utils.constrain_str(item)
    except Exception:
        return "a thing..."


def _construct_event_from_notion(date: arrow.Arrow, activity_type: _ActivityType, page_description: str,
                                 url: str) -> StreamEvent:
    has_public_url = requests.get(url).status_code == 200
    text = utils.make_anchor_tag(url, page_description) if has_public_url else page_description
    return StreamEvent(StreamVendorName.Notion, date, f"{activity_type.name} {text}")


def get_notion_updates(start_date: arrow.Arrow, items=[], starting_after_id=None) -> List[StreamEvent]:
    item_request_limit = 20
    req_data = {"spaceId": env.NOTION_SPACE_ID, "limit": item_request_limit}
    req_data = {**req_data, "startingAfterId": starting_after_id} if starting_after_id else req_data
    result = client.post('/api/v3/getActivityLog', req_data)

    # TODO: adjust starting ID recurse...
    resp = result.json()
    record_map = resp["recordMap"]

    # NOTE: don't need this if we are validating every URL in series
    # time.sleep(0.5)  # avoid getting rate-limited because there is no code to handle that

    new_items: List[StreamEvent] = []
    for key, val in record_map["activity"].items():
        activity = val["value"]
        date = arrow.get(int(activity["start_time"]))
        if date <= start_date:
            continue
        activity_type = _convert_activity_type(activity["type"])
        url = _construct_notion_url(record_map, activity)
        if activity_type and _activity_is_user(record_map, activity):
            description = _make_description_of_activity(activity)
            new_items.append(_construct_event_from_notion(date, activity_type, description, url))

    need_more = len(new_items) == item_request_limit
    all_items = new_items + items

    if len(all_items) >= MAX_ITEMS_TO_FETCH:
        # useful for first time run
        return all_items

    last_id = list(record_map["activity"].keys())[-1]
    return get_notion_updates(start_date, items=all_items, starting_after_id=last_id) \
        if need_more else new_items + items
