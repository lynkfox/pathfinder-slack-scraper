#!/usr/bin/env python3
import os

import aws_cdk as cdk

from configurations.common import DeploymentProperties
from stacks.pathfinder_scraper_main_stack import MainStack

app = cdk.App()
default_environment = cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION"))
deployment_props = DeploymentProperties()
MainStack(
    app,
    deployment_props.prefix_name("PFScraper"),
    env=default_environment,
    deployment_properties=deployment_props,
)
app.synth()
