import os
import json
from slack_sdk.errors import SlackApiError
from aws_lambda_powertools import Logger
from slack_integration import slack_client_factory, get_messages, parse_message
from helpers import get_week_start_end_datetimes, convert_week_bookends_to_timestamps
from models.lambda_event import ApiEvent, IncomingEvent
from models.scanner_data import Scanner, scanner_eve_mail_link, scanner_payout
from datetime import datetime, timedelta, date
import time
from common.attributes import DynamoAttributes, ScannerScrapeKeys
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal


logger = Logger()

CHANNEL_NAME = "pathfinder-scanning-scrape"
CONVERSATION_ID = "C05JHL0LBNC"
TOKEN = os.getenv("SLACK_TOKEN", "Not Set yet")
CACHE_TABLE = os.getenv("DYNAMO_CACHE", "Oops not set")
CACHE_TTL = os.getenv("CACHE_TTL", 6)
UPDATE_RESULTS_LAMBDA = os.getenv("UPDATE_RESULTS_LAMBDA", "uhoh")

db_client = boto3.resource('dynamodb')

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
                target_week = _event.week_number
                logger.append_keys(week_api_modifier=target_week)
                logger.info("/week/# api called. Finding week #")

            
            logger.append_keys(target_week=target_week, target_year=target_year, path_parts=_event.path_parts)


            existing = check_cache(CACHE_TABLE, target_week)

            if existing is None:
                CLIENT = slack_client_factory(TOKEN)
                logger.info("Slack Client initialized")
                # TODO: make Full_audit achievable through API
                status_code, body = retrieve_and_process_week(CLIENT, target_week, full_audit=False)
                body[ScannerScrapeKeys.CACHED] = datetime.now().isoformat()
                add_ttl =  _event.api_event == ApiEvent.THIS_WEEK or date.today().isocalendar().week == target_week
                logger.info("Add TTL?", extra={"ttl_flag": add_ttl})
                cache_result(CACHE_TABLE, target_week, body, use_timestamp=add_ttl)
    
            else:
                status_code = 200
                body = existing
            
            
        body[ScannerScrapeKeys.EVE_MAIL_OUTPUT] = build_email_links(body[ScannerScrapeKeys.INDIVIDUAL_TOTALS], total_payout=_event.total_payout)


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
            "body": json.dumps(body, default=default_type_error_handler),
        }

def retrieve_and_process_week(client, target_week, full_audit:bool=False):

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

    logger.info("Messages Parsed")

    for scanner in all_scanners.values():
        scanner.filter_non_valid_sigs(non_valid_sigs)

    logger.info("Non Valid sigs filtered")

    return build_response(start_date, end_date, all_scanners, full_audit)


def value_per_sig(total_payout, total_sigs):
    return float(total_payout)/int(total_sigs)

def build_response(start_date, end_date, all_scanners, full_audit):
    audit = {key: value.get_audit(full_audit) for key, value in all_scanners.items()}
    reduced_scanners = {key: value.total_sigs for key, value in all_scanners.items()}
    reduced_scanners[ScannerScrapeKeys.TOTAL_SIGS] = sum([scanner.total_sigs for scanner in all_scanners.values()])

    body = {ScannerScrapeKeys.WEEK:{"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, ScannerScrapeKeys.INDIVIDUAL_TOTALS: reduced_scanners, ScannerScrapeKeys.AUDIT: audit}
    status_code = 200

    logger.append_keys(scanner_totals=reduced_scanners, status_code=status_code)

    logger.info("Response Built")
    return status_code, body


def build_email_links(all_scanners:list, total_payout:int) -> str:
    
    is_isk_payout = float(total_payout) > 0
    payout_type = "million isk" if is_isk_payout else "sites"

    if type(all_scanners) is list and type(all_scanners[0]) is Scanner:
        per_sig = value_per_sig(total_payout, sum([scanner.total_sigs for scanner in all_scanners.values()]))
        
        return  " <br> ".join([f"{scanner_eve_mail_link(scanner.name)} - {scanner_payout(per_sig, scanner.total_sigs)} {payout_type}" for scanner in all_scanners.values() if scanner.total_sigs > 0])
    elif type(all_scanners) is dict:
        per_sig = value_per_sig(total_payout, all_scanners[ScannerScrapeKeys.TOTAL_SIGS])
        return  " <br> ".join([f"{scanner_eve_mail_link(name)} - {scanner_payout(per_sig, total)} {payout_type}" for name, total in all_scanners.items() if total > 0 and name != "TOTAL_SIGS"])

def check_cache(table_name, week):

    week = build_pk(week)
    table = db_client.Table(table_name)
    response = table.query(
        KeyConditionExpression=Key(DynamoAttributes.PARTITION_KEY).eq(str(week))
    )
    cache_response = response.get("Items", [])

    if len(cache_response) <= 0:
        logger.info("No cache found, will calculate")
        return None
    
    latest_cache = cache_response[-1]
    
    cache_updated = datetime.fromisoformat(latest_cache[DynamoAttributes.DATE_UPDATED])

    time_difference = datetime.now()-cache_updated
    logger.append_keys(cache_last_updated=cache_updated)
    # hours to seconds 
    if time_difference.seconds >= CACHE_TTL*60*60 and week >= date.today().isocalendar().week: 
        logger.info(f"Cache is older than {CACHE_TTL} hours, will calculate")
        return None
    
    logger.info(f"Cache is under {CACHE_TTL} hours, using it")
    return latest_cache[DynamoAttributes.BODY] 


def cache_result(table_name, week, body, use_timestamp=False):
    table = db_client.Table(table_name)

    date_updated = datetime.now()

    cache_body = {
            DynamoAttributes.PARTITION_KEY: str(build_pk(week)),
            DynamoAttributes.SORT_KEY: date_updated.isoformat(),
            DynamoAttributes.WEEK_NUMBER: week,
            DynamoAttributes.DATE_UPDATED: date_updated.isoformat(),
            DynamoAttributes.BODY: body,
        }
    

    if use_timestamp:
        ttl_datetime = date_updated + timedelta(hours=24)
        ttl_timestamp = time.mktime(ttl_datetime.timetuple())
        cache_body[DynamoAttributes.TIME_TO_LIVE] = Decimal(ttl_timestamp)
        logger.append_keys(ttl_timestamp=ttl_datetime.isoformat())
    
    

    logger.append_keys(cache_updated=date_updated.isoformat())
    table.put_item(
        Item=cache_body
    )
    logger.debug("Cache Updated")






def default_type_error_handler(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    return f"Unparsable Type: {type(obj)}"

def build_pk(week):
    if week is None or week == 0:
        return date.today().isocalendar().week
    if int(week) < 0:
        return date.today().isocalendar().week+week

    return week