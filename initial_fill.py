from local_setup_env import setup_local_env

setup_local_env(local_db=False)

import arrow


from activity_log_aggregation import db
from activity_log_aggregation.streams.github import get_github_updates
from activity_log_aggregation.streams.notion import get_notion_updates
from activity_log_aggregation.streams.stream_event import StreamVendorName

fallback_date = arrow.get(2021, 1, 8)

last_github_log_date = db.get_most_recent_activity_date_by_vendor(StreamVendorName.Github)
last_notion_log_date = db.get_most_recent_activity_date_by_vendor(StreamVendorName.Notion)
github_activity_logs = get_github_updates(last_github_log_date or fallback_date)
notion_activity_logs = get_notion_updates(last_notion_log_date or fallback_date)
db.write_activity_logs(github_activity_logs + notion_activity_logs)
