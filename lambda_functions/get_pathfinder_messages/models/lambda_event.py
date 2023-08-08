
from dataclasses import dataclass, field
from enum import Enum
from aws_lambda_powertools import Logger

logger = Logger()

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
    week_number: int = field(init=False)
    total_payout: float = field(init=False)
    path_parts: list = field(init=False)
    IS_OPTIONS: bool = field(init=False)
    IS_GET: bool = field(init=False)
    IS_POST: bool = field(init=False)
    api_type: str = field(init=False)

    def __post_init__(self):
        self.path = self.event.get("resource", "")
        self.determine_event()
        self.determine_type()
        self._is_allowed_method()
    
    def determine_event(self):

        dispatch = {
            "/v1/week/{proxy+}": ApiEvent.A_WEEK,
            "/v1/lastweek/{proxy+}": ApiEvent.LAST_WEEK,
            "/v1/thisweek/{proxy+}": ApiEvent.THIS_WEEK,
            "/v1/lastweek": ApiEvent.LAST_WEEK,
            "/v1/thisweek": ApiEvent.THIS_WEEK
        }

        
        self.api_event = dispatch[self.path]

        self._parse_path_parts()



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
        
    def _parse_path_parts(self):
        logger.info(f"Parsing Proxy paths {self.event}")
        try:
            self.path_parts = self.event.get("pathParameters", {}).get("proxy", "")
        
            parts = self.path_parts.split("/")
            number_of_proxy_paths = len(parts)
            self.total_payout = 0
            
            if self.api_event == ApiEvent.A_WEEK:
                self.week_number = parts[0]
                if number_of_proxy_paths == 2:
                    self.total_payout=parts[1]

            elif number_of_proxy_paths == 1:
                self.total_payout = parts[0]

        except:
            logger.info("No Proxy parameters found)")
            self.path_parts = ""
            self.total_payout = 0
            self.week_number = self.api_event.value

        

        