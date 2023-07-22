from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class ResourceNames:
    ITEM_DYNAMODB: ClassVar[str] = field(init=False, default="cached-updates")
    BACKEND_API: ClassVar[str] = field(init=False, default="PFScanners")
    GET_WEEK_RESULTS: ClassVar[str] = field(init=False, default="GetWeekScanners")
    COMMON_LAYER: ClassVar[str] = field(init=False, default="common")


@dataclass(frozen=True)
class DirectoryLocations:
    GET_WEEK_RESULTS: ClassVar[str] = field(init=False, default="lambda_functions/get_pathfinder_messages")
    COMMON_LAYER: ClassVar[str] = field(init=False, default="common.zip")


@dataclass(frozen=True)
class Environment:
    DEMO: ClassVar[str] = field(init=False, default="DEMO")
    DEV: ClassVar[str] = field(init=False, default="DEV")
    PROD: ClassVar[str] = field(init=False, default="PROD")
