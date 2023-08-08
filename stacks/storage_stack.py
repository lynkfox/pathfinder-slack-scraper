import aws_cdk as core
from aws_cdk import NestedStack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct
from common.attributes import DynamoAttributes

from configurations import ResourceNames
from configurations.common import DeploymentProperties


class StorageStack(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, deployment_properties: DeploymentProperties, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """
            Contains the Storage Resources such as S3, Dynamodb, Parameter/Secrets
        """
        props = deployment_properties

        self.cache_db = dynamodb.Table(self, "WeeklyResultStorage",
                                       table_name="PFScannerCache",
                                       removal_policy=core.RemovalPolicy.DESTROY,
                                       time_to_live_attribute=DynamoAttributes.TIME_TO_LIVE,
                                       partition_key=dynamodb.Attribute(name=DynamoAttributes.PARTITION_KEY, type=dynamodb.AttributeType.STRING),
                                       sort_key=dynamodb.Attribute(name=DynamoAttributes.SORT_KEY, type=dynamodb.AttributeType.STRING))