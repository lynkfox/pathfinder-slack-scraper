from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class DynamoAttributes:
    PARTITION_KEY: ClassVar[str] = "pk"
    SORT_KEY: ClassVar[str] = "sk"
    TIME_TO_LIVE: ClassVar[str] = "ttl"
    DATE_UPDATED: ClassVar[str] = "dateUpdated"
    WEEK_NUMBER: ClassVar[str] = "weekNumber"
    BODY: ClassVar[str] = "body_response"


@dataclass(frozen=True)
class ScannerScrapeKeys:
    WEEK: ClassVar[str] = "week"
    INDIVIDUAL_TOTALS: ClassVar[str] = "totals"
    TOTAL_SIGS: ClassVar[str] = "TOTAL_SIGS"
    EVE_MAIL_OUTPUT: ClassVar[str] = "paste_in_eve_mail"
    AUDIT: ClassVar[str] = "audit"
    VALID_SIGS: ClassVar[str] = "valid_sigs"
    CACHED: ClassVar[str] = "cached_at"