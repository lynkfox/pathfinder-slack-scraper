from configurations import Environment
from dataclasses import dataclass, field


@dataclass
class LambdaEnvironmentVariables:
    unique_env: dict
    lambda_name: str
    log_level: str = field(default="DEBUG")
    environment: str = field(default=Environment.DEMO)

    def as_dict(self):
        return {
            **self.unique_env,
            **{"POWERTOOLS_SERVICE_NAME": self.lambda_name, "LOG_LEVEL": self.log_level},
        }
