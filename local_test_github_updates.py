from local_setup_env import setup_local_env

setup_local_env()

import arrow

from activity_log_aggregation.streams.github import get_github_updates

date = arrow.get(2021, 1, 8)

results = get_github_updates(date)

print('len github results', len(results))
for result in results:
    print(result.basic_html)
