
from aws_lambda_powertools import Logger
import os
import json
from lambda_functions.get_pathfinder_messages.slack_integration import slack_client_factory
from lambda_functions.get_pathfinder_messages.index import retrieve_and_process_week
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
logger = Logger()
channel_name = "pathfinder-scanning-scrape"
CONVERSATION_ID = "C05JHL0LBNC"
target_week = None

with open("config.json", "r") as f:
    config_file = json.load(f)
    SLACK_TOKEN = config_file["token"]



CLIENT = slack_client_factory(SLACK_TOKEN)

status_code, body = retrieve_and_process_week(CLIENT, target_week)


#save results
with open("slack_results.json", "w") as f:
    json.dump(body, f)

