from dataclasses import dataclass

import arrow
import boto3
import math
import asyncio
from typing import Optional, List
from boto3.dynamodb.conditions import Key

from activity_log_aggregation import utils
from activity_log_aggregation.streams.stream_event import StreamVendorName, StreamEvent
from activity_log_aggregation.utils.env import DYNAMODB_CLIENT_CONFIG, DYNAMODB_TABLE_NAME

dynamodb = boto3.resource('dynamodb', **DYNAMODB_CLIENT_CONFIG)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

PRIMARY_KEY = "PK"
SORT_KEY = "SK"
GSI1_SORT_KEY = "TypeSK"
MAX_PARALLEL_DYNAMODB_REQUESTS = 10


@dataclass
class ActivityLog:
    vendor_type: StreamVendorName
    date: arrow.Arrow
    basic_html: str


def _ensure_utc(date: arrow.Arrow) -> arrow.Arrow:
    return date.to("utc")


def _date_to_pk(date: arrow.Arrow) -> str:
    return _ensure_utc(date).format('YYYY-MM-DD')


def _get_millis(date: arrow.Arrow) -> int:
    s = date.timestamp()
    ms = int(date.format("SSS"))
    return math.floor((s * 1000) + ms)


def _validate_start_end(start: arrow.Arrow, end: arrow.Arrow):
    if start > end:
        raise Exception("Start time can't be after end time!")


def _get_pks_in_range(start: arrow.Arrow, end: arrow.Arrow) -> List[str]:
    _validate_start_end(start, end)
    pks = set()
    while start <= end:
        pks.add(_date_to_pk(start))
        start = start.shift(days=1)
    pks.add(_date_to_pk(end))
    return sorted(list(pks))


def get_most_recent_activity_date_by_vendor(stream_vendor: StreamVendorName) -> Optional[arrow.Arrow]:
    MAX_NUM_DAYS_TO_CHECK = 14
    start_date = arrow.utcnow()

    while MAX_NUM_DAYS_TO_CHECK >= 0:
        response = table.query(IndexName='GSI1',
                               KeyConditionExpression=Key(PRIMARY_KEY).eq(_date_to_pk(start_date)) &
                                                      Key(GSI1_SORT_KEY).begins_with(stream_vendor.name),
                               ScanIndexForward=False)
        if len(response.get("Items", [])) > 0:
            # structure of GSI1_SORT_KEY is like `Notion#1621394799576#s9df09fis`
            return arrow.get(int(response["Items"][0][GSI1_SORT_KEY].split("#")[1]))

        MAX_NUM_DAYS_TO_CHECK -= 1
        start_date = start_date.shift(days=-1)

    return None


def _get_activity_logs_for_pk(pk: str, start: arrow.Arrow) -> List[ActivityLog]:
    # TODO: `start` arg really shouldn't be required here, should probably just pass in sort condition?
    logs = []
    response = table.query(KeyConditionExpression=Key(PRIMARY_KEY).eq(pk) &
                                                  Key(SORT_KEY).gte(str(_get_millis(start))))
    for item in response["Items"]:
        # SK looks like `1621209622452#d39ccde6552fda2ff7a3359c0816be4a`
        date = arrow.get(int(item["SK"].split("#")[0]))
        vendor_type = StreamVendorName[item["Type"]]
        logs.append(ActivityLog(vendor_type, date, item["BasicHtml"]))
    return logs


def get_logs(start: arrow.Arrow, end: Optional[arrow.Arrow] = None, filter_vendors: List[StreamVendorName] = None, desc=False) -> \
        List[ActivityLog]:
    end = end or arrow.utcnow()
    if filter_vendors:
        raise NotImplementedError()
    _validate_start_end(start, end)

    # TODO: implement pagination

    # TODO: implement this as parallel, NOTE parallelism in python SUCKS
    logs: List[ActivityLog] = []
    for pk in _get_pks_in_range(start, end):
        logs += _get_activity_logs_for_pk(pk, start)
    logs.sort(key=lambda x: x.date,
              reverse=desc)  # TODO: Setting this on the DB return could be slightly more optimal
    return logs


def write_activity_logs(activity_logs: List[StreamEvent]):
    composite_keys = set()
    with table.batch_writer() as batch:
        for log in activity_logs:
            utc_date = _ensure_utc(log.date)
            utc_date_ms = _get_millis(utc_date)
            hash_id = utils.hash_str(log.basic_html)
            pk = _date_to_pk(utc_date)
            sk = f"{utc_date_ms}#{hash_id}"

            # since `batch_writer` can't deal with duplicates, we have to de-dupe here
            composite_key = pk + sk
            if composite_key in composite_keys:
                continue
            composite_keys.add(composite_key)

            batch.put_item(Item={
                'PK': pk,
                'SK': sk,
                'Type': log.name.name,
                'TypeSK': f"{log.name.name}#{utc_date_ms}#{hash_id}",
                'BasicHtml': log.basic_html
            })
