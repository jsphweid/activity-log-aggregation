import arrow
import json

from activity_log_aggregation import db
from activity_log_aggregation.db import ActivityLog


def convert_log(log: ActivityLog) -> dict:
    # TODO: implement a more generic solution
    return {
        "vendorType": log.vendor_type.name,
        "date": log.date.isoformat(),
        "basicHtml": log.basic_html
    }


def parse_date_arg(arg: str) -> arrow.Arrow:
    try:
        # if like '1238123
        arg = int(arg)
    except ValueError:
        # or actual string date that is immediately parsable by arrow
        pass
    return arrow.get(arg)


def handler(event, _):
    params = event['queryStringParameters']
    start = parse_date_arg(params.get('start'))
    end = parse_date_arg(params['end']) if params.get('end') else None
    results = db.get_logs(start, end, desc=True)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(list(map(convert_log, results)))
    }
