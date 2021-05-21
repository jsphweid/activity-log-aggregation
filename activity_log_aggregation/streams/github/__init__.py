import arrow
from github import Github

from activity_log_aggregation import utils
from activity_log_aggregation.streams.stream_event import StreamEvent, StreamVendorName
from activity_log_aggregation.utils import env


def _format_repo_url(url: str) -> str:
    # The only URL in the HTTP API is an api URL and not an html URL
    # This function simply converts it to the HTML URL
    url = url.replace("api.", "")
    url = url.replace("repos/", "")
    return url


def _format_commit_url(url: str) -> str:
    url = _format_repo_url(url)
    url = url.replace("commits/", "commit/")
    return url


def _format_event(event: dict):
    event_type = event["type"]
    payload = event["payload"]
    repo = event["repo"]
    repo_url = _format_repo_url(repo["url"])
    name = StreamVendorName.Github
    action = payload.get("action", "").capitalize()
    base_args = {"name": name, "date": arrow.get(event["created_at"])}
    if event_type == "IssuesEvent":
        return StreamEvent(
            **base_args,
            basic_html=f'{action} issue on {utils.make_anchor_tag(_format_repo_url(payload["issue"]["url"]), repo["name"])}')
    elif event_type == "IssueCommentEvent":
        return StreamEvent(
            **base_args,
            basic_html=f'{action} issue comment on {utils.make_anchor_tag(payload["comment"]["html_url"], repo["name"])}')
    elif event_type == "WatchEvent":
        return StreamEvent(
            **base_args,
            basic_html=f'{action} watching {utils.make_anchor_tag(repo_url, repo["name"])}')
    elif event_type == "DeleteEvent":
        return StreamEvent(
            **base_args,
            basic_html=f'Deleted {payload["ref_type"]} {payload["ref"]} on {utils.make_anchor_tag(repo_url, repo["name"])}')
    elif event_type == "PullRequestEvent":
        text = f'pull request on {repo["name"]}'
        return StreamEvent(**base_args, basic_html=f'{action} {utils.make_anchor_tag(repo_url, text)}')
    elif event_type == "CreateEvent":
        return StreamEvent(
            **base_args,
            basic_html=f'Created {payload["ref_type"]} {payload["ref"]} on {utils.make_anchor_tag(repo_url, repo["name"])}')
    elif event_type == "ForkEvent":
        fork_name, fork_url = payload["forkee"]["full_name"], payload["forkee"]["html_url"]
        return StreamEvent(
            **base_args,
            basic_html=f'Forked {utils.make_anchor_tag(repo_url, repo["name"])} into {utils.make_anchor_tag(fork_url, fork_name)}')
    elif event_type == "PushEvent":
        commits = [
            f'{utils.constrain_str(c["message"])} ' \
            f'({utils.make_anchor_tag(_format_commit_url(c["url"]), utils.constrain_str(c["sha"], max_length=12, add_dots=False))})'
            for c in payload["commits"]]
        commits_chunk = "<ul>" + "".join(["<li>" + c + "</li>" for c in commits]) + "</ul>"
        opener = f'Pushed new commits to {utils.make_anchor_tag(repo_url, repo["name"])}'
        return StreamEvent(**base_args, basic_html=f'{opener}</br>{commits_chunk}')
    else:
        # NOTE: if you get this, an easy way to debug the event that isn't handled would be to
        # execute this https://api.github.com/users/{GITHUB_USERNAME}/events and find the missing one
        # or maybe just get all from https://docs.github.com/en/developers/webhooks-and-events/github-event-types
        return StreamEvent(**base_args, basic_html=f"Did something on Github... ({event_type})")


def get_github_updates(date: arrow.Arrow):
    github = Github(login_or_token=env.GITHUB_ACCESS_TOKEN)
    new_events = []
    unique_types = set()
    for event in github.get_user(env.GITHUB_USER).get_events():
        unique_types.add(event.type)
        if arrow.get(event.created_at) <= date:
            return new_events
        new_events.append(_format_event(event.raw_data))  # temp
    return new_events
