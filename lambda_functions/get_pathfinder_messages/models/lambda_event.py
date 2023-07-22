
from dataclasses import dataclass, field
from enum import Enum

class ApiEventTypes(Enum):
    CORS_PREFLIGHT = "OPTIONS"
    GET = "GET"
    POST = "POST"

class ApiEvent(Enum):
    A_WEEK = "week"
    THIS_WEEK = "thisweek"
    LAST_WEEK = "last_week"

@dataclass
class IncomingEvent:
    event: dict
    path: str = field(init=False)
    api_event: ApiEvent = field(init=False)
    path_parts: list = field(init=False)
    IS_OPTIONS: bool = field(init=False)
    IS_GET: bool = field(init=False)
    IS_POST: bool = field(init=False)
    api_type: str = field(init=False)

    def __post_init__(self):
        self.path = self.event.get("resource", "")
        self.determine_event()
        if self.api_event == ApiEvent.A_WEEK:
            self.path_parts = self.event.get("pathParameters", {}).get("proxy", "")
        else:
            self.path_parts = ""
        self.determine_type()
        self._is_allowed_method()
    
    def determine_event(self):
        dispatch = {
            "/v1/week/{proxy+}": ApiEvent.A_WEEK,
            "/v1/lastweek": ApiEvent.LAST_WEEK,
            "/v1/thisweek": ApiEvent.THIS_WEEK
        }

        self.api_event = dispatch[self.path]

    def determine_type(self):
        """
        determines the type of the api call
        """

        self.method = self.event.get("httpMethod")

        self.IS_GET = self.method == ApiEventTypes.GET.value
        self.IS_OPTIONS = self.method == ApiEventTypes.CORS_PREFLIGHT.value
        self.IS_POST = self.method == ApiEventTypes.POST.value

    def _is_allowed_method(self):
        """
        GetEntity only allows Options and Get method calls.
        """
        if self.IS_OPTIONS:
            self.api_type = ApiEventTypes.CORS_PREFLIGHT

        elif self.IS_GET:
            self.api_type = ApiEventTypes.GET

        else:
            raise TypeError("Not a valid Type for GetEntity - must be GET or OPTIONS")