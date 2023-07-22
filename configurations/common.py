from dataclasses import dataclass, field
from aws_cdk import aws_ec2 as ec2
from typing import Optional, List
import json


@dataclass
class DeploymentProperties:
    PREFIX: str = field(default="PFScanner")
    ENVIRONMENT: str = field(default=None)
    SLACK_TOKEN: str = field(init=False, default=None)
    vpc: Optional[ec2.IVpc] = field(default=None)
    security_groups: Optional[List[ec2.SecurityGroup]] = field(default_factory=list)

    def __post_init__(self):
        with open("config.json", "r") as f:
            self.config_file = json.load(f)

        self.get_api_token()
        

    def get_api_token(self):
        self.SLACK_TOKEN = self.config_file["token"]


    def prefix_name(self, name: str, lower: bool = False) -> str:
        """
        Returns the name-tag ready to be prefixed on a resource

        Parameters:
            name(str): Name of the resource.
            lower(bool) [Optional]: Defaults False, set true for resources like S3.

        Returns:
            (str): Name prefixed with Prefix and Environment with dashes between.
        """
        deployment_env = f"{self.ENVIRONMENT}-" if self.ENVIRONMENT is not None else ""
        full_name = f"{self.PREFIX}-{deployment_env}{name}"
        return full_name.lower() if lower else full_name

    def add_security_group(self, security_group: ec2.SecurityGroup) -> None:
        """
        Adds a Security group to the list
        """
        self.security_groups.append(security_group)
