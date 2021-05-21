from activity_log_aggregation import db
from activity_log_aggregation.streams.github import get_github_updates
from activity_log_aggregation.streams.notion import get_notion_updates
from activity_log_aggregation.streams.stream_event import StreamVendorName

tasks = [
    (StreamVendorName.Github, get_github_updates),
    (StreamVendorName.Notion, get_notion_updates)
]


def handler(_, __):
    activity_logs_to_add = []
    for vendor, getter in tasks:
        logs = getter(db.get_most_recent_activity_date_by_vendor(vendor))
        print(f"{len(logs)} {vendor.name} logs found that need to be added...")
        activity_logs_to_add.extend(logs)

    print(f"Writing {len(activity_logs_to_add)} activity logs to the DB...")
    db.write_activity_logs(activity_logs_to_add)
