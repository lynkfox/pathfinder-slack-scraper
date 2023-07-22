import os
from pathlib import Path

import aws_cdk as core
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from configurations.common import DeploymentProperties
from stacks.storage_stack import StorageStack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import ApiStack

root_directory = Path(__file__).parents[1]


class MainStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_properties: DeploymentProperties,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.props = deployment_properties

        vpc = ec2.Vpc.from_lookup(self, "VPCFromLookup", is_default=True)

        # vpc = ec2.Vpc(
        #     self,
        #     "VPC",
        #     nat_gateways=0,
        #     subnet_configuration=[
        #         ec2.SubnetConfiguration(name="tracker-public", subnet_type=ec2.SubnetType.PUBLIC),
        #         ec2.SubnetConfiguration(name="tracker-isolated", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
        #     ],
        # )
        # vpc.apply_removal_policy(core.RemovalPolicy.DESTROY)

        self.props.vpc = vpc

        storage = StorageStack(self, "StorageStack", self.props)

        functions = LambdaStack(self, "Lambdas", self.props, None)

        api = ApiStack(self, "Api", self.props, functions.lambda_mapping)

        core.CfnOutput(
            self,
            "ApiEndpoint",
            value=api.backend_api.url,
        )

