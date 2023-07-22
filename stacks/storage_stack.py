import aws_cdk as core
from aws_cdk import NestedStack
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct

from configurations import ResourceNames
from configurations.common import DeploymentProperties


class StorageStack(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, deployment_properties: DeploymentProperties, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """
            Contains the Storage Resources such as S3, Dynamodb, Parameter/Secrets
        """
        props = deployment_properties

