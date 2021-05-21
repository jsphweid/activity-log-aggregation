# activity-log-aggregation


# Security note
To get this project up and running quickly, I formulated the HTML that is displayed on the backend. This
is convenient because at the time of extraction from Github/Notion/etc., the structure of how something
should be displayed is most obvious at that point. So I decided to formulate the `basic_html` there
and save it in the DB. While this is the easiest, it's not the safest. If someone strategically were to
somehow mess with the datasources I'm pulling from (maybe put some <script> in a Notion doc), it could
be stored in my DB and rendered dangerously for anyone coming to my site. For this reason I have a very primitive
sanitization function `_contains_potentially_malicious_html` designed to prevent potentially malicious html from
entering the DB.

In the future I may take more time in engineering a universally safer and more standard option.

For another layer of protection, I'm using `DOMPurify` on the frontend.


## Setup for run/deploy
You need to have a file `prod.env` at the root that looks like:
```bash
GITHUB_ACCESS_TOKEN=ghp_SGeMGL8ntblahblahblah
GITHUB_USER=someuser
NOTION_EMAIL=someuserd@gmail.com
NOTION_TOKEN_V2=4f854683138becd68ffb9esjdofisdiblahblahblah
NOTION_SPACE_ID=3d36d5cd-cca4-4bc5-blah-blahblahblah
```