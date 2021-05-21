from dataclasses import dataclass
from enum import Enum

import arrow


class StreamVendorName(Enum):
    Notion = "Notion"
    Github = "Github"


@dataclass
class StreamEvent:
    name: StreamVendorName
    date: arrow.Arrow
    basic_html: str
