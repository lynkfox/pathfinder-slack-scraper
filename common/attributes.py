from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class DynamoAttributes:
    PARTITION_KEY: ClassVar[str] = "pk"
    SORT_KEY: ClassVar[str] = "sk"
    SIGNATURE_ID: ClassVar[str] = "sigID"
    NAME: ClassVar[str] = "name"
    DATE_UPDATED: ClassVar[str] = "dateUpdated"
    WEEK_NUMBER: ClassVar[str] = "weekNumber"