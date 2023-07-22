import os
import json
from slack_sdk.errors import SlackApiError
from aws_lambda_powertools import Logger
from slack_integration import slack_client_factory, get_messages, parse_message
from helpers import get_week_start_end_datetimes, convert_week_bookends_to_timestamps
from models.lambda_event import ApiEvent, IncomingEvent


logger = Logger()

CHANNEL_NAME = "pathfinder-scanning-scrape"
CONVERSATION_ID = "C05JHL0LBNC"
TOKEN = os.getenv("SLACK_TOKEN", "Not Set yet")

@logger.inject_lambda_context(log_event=True, clear_state=True)
def lambda_handler(event: dict, context: dict) -> dict:
    """
    Parses incoming webhook from Pathfinder with Map Update changes, determines if it is an update, and if new places it in the dynamo
    """
    
    body = {}
    status_code = 502

    try:

        logger.debug("Processing Event")
        _event = IncomingEvent(event)
        body = json.dumps({"message": "Invalid format"})

        if _event.IS_OPTIONS:
            #check_approved_preflight_cors(event)
            body = json.dumps({"message": "Preflight Accepted"})

        else:
            logger.info("Get Call")

            target_week = None
            target_year = None

            if _event.api_event == ApiEvent.LAST_WEEK:
                target_week = -1
                logger.append_keys(week_api_modifier="-1")
                logger.info("/lastweek api called. setting to -1")
            
            elif _event.api_event == ApiEvent.THIS_WEEK:
                target_week = None
                logger.append_keys(week_api_modifier="None")
                logger.info("/thisweek api called. setting to None")

            elif _event.api_event == ApiEvent.A_WEEK:
                
                target_week = _event.path_parts
                logger.append_keys(week_api_modifier=target_week)
                logger.info("/week/# api called. Finding week #")

            
            logger.append_keys(target_week=target_week, target_year=target_year, path_parts=_event.path_parts)

            CLIENT = slack_client_factory(TOKEN)
            logger.info("Slack Client initialized")


            status_code, body = retrieve_and_process_week(CLIENT, target_week)
            

    except SlackApiError as e:
        logger.exception("Failure in slack", stack_info=True)
        body = e
        status_code = 503

    except Exception as e:
        logger.exception("Other Exception", stack_info=True)
        body = e
        status_code = 503

    finally:
        logger.append_keys(response_status_code=status_code, response_body=body)
        logger.info("returning")
        return {
            "statusCode": status_code,
            "headers": {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET",
            },
            "body": json.dumps(body),
        }

def retrieve_and_process_week(client, target_week):

    start_date, end_date = get_week_start_end_datetimes(week=target_week, year=None)
    logger.append_keys(start_date=start_date.isoformat(), end_date=end_date.isoformat())

    start_timestamp, end_timestamp = convert_week_bookends_to_timestamps(start_date, end_date)
    logger.append_keys(start_timestamp=start_timestamp, end_timestamp=end_timestamp)
            
    conversation_history = get_messages(CONVERSATION_ID, client, start_timestamp, end_timestamp)

    logger.append_keys(message_count=len(conversation_history))
    logger.info("Messages retrieved from Slack Channel")
    all_sigs = {}
    all_scanners = {}
    non_valid_sigs = []
    

    for message in conversation_history:
        if message.get("type", "") != "message" or message.get("subtype", "") != "bot_message":
            continue
        parse_message(message, all_scanners, all_sigs, non_valid_sigs )

    logger.info("Messages Parsed and calculated")

    status_code, body = build_response(start_date, end_date, all_sigs, all_scanners)

    return status_code, body

def build_response(start_date, end_date, all_sigs, all_scanners):
    audit = {key: value.get_audit(all_sigs) for key, value in all_scanners.items()}
    reduced_scanners = {key: value.total_sigs for key, value in all_scanners.items()}

    body = {"week":{"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "totals": reduced_scanners, "audit": audit}
    status_code = 200

    logger.append_keys(scanner_totals=reduced_scanners, status_code=status_code)
    return status_code, body
