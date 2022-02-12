from local_setup_env import setup_local_env

setup_local_env(local_db=False)

from lambdas.fetch_lambda import convert_log
from activity_log_aggregation import db
from activity_log_aggregation.streams.stream_event import StreamVendorName

# result = db.get_most_recent_activity_date_by_vendor(StreamVendorName.Notion)
import arrow


# result = db._get_pks_in_range(arrow.get(2021, 5, 13), arrow.get(2021, 5, 20))
# print('result', result)

def f():
    result = db.get_logs(arrow.get("2021-05-18T14:31:12.160Z"), None, desc=True)
    print('result', result)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': list(map(convert_log, result))
    }

# 2021-05-12T00:00:00.000Z&end=2021-05-17T00:00:00.000Z
result = db.get_logs(arrow.get("2021-05-12T00:00:00.000Z"), arrow.get("2021-05-17T00:00:00.000Z"), limit=None)
print('result', result[0:5])


w = db.get_most_recent_activity_date_by_vendor(StreamVendorName.Notion)
print('w', w)
