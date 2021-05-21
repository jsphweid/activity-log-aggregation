from local_setup_env import setup_local_env

setup_local_env(local_db=False)

import arrow

from activity_log_aggregation import db
from activity_log_aggregation.streams.stream_event import StreamVendorName
from activity_log_aggregation.streams.notion import get_notion_updates

# date = arrow.get(2021, 1, 8)
date = db.get_most_recent_activity_date_by_vendor(StreamVendorName.Notion)
print('date', date)
results = get_notion_updates(date)

print('len notion results', len(results))
for result in results:
    print(result.basic_html)
