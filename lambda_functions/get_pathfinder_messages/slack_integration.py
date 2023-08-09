
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from models.slack_messages import SlackMessage
from models.scanner_data import Scanner, Signature, GroupID
from typing import Union, Dict, List
from aws_lambda_powertools import Logger
from helpers import parse_attachement, create_unique_sig_name, parse_for_value_of
from sig_and_scanner_parse import update_signatures, update_scanner

logger = Logger()



# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.


def slack_client_factory(token):
    return WebClient(token=token)


def get_channel(client, channel_name, conversation_id):
    """
    get_channel is used to find the channel ID name. Recomended only to use in local and then set channel id name as env variable or global.
    """

    try:
        for result in client.conversations_list():
            if conversation_id is not None:
                break
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    conversation_id = channel["id"]
                    break
        return conversation_id
    
    except SlackApiError as e:
        logger.exception(f"Error: {e}")
        raise e


def get_messages(client, conversation_id: str, start_timestamp, end_timestamp):
    """
    get_messages connects to slack itegration and pulls the messages from channel coversation history, using the start and end timestamps.
    It will loop over paginated results automatically, and return a list of message jsons.
    """
    try:
        result = client.conversations_history(channel=conversation_id, oldest=start_timestamp, latest=end_timestamp, inclusive=True)

        tmp = result["messages"]
        conversation_history = tmp
        
        more = result.get("has_more", False)
        page=1
        while more:
            last_timestamp = tmp[-1]["ts"]
            page += 1
            new_result = client.conversations_history(channel=conversation_id, oldest=start_timestamp, latest=last_timestamp, inclusive=True,)
            conversation_history.extend(new_result["messages"])
            more = new_result.get("has_more", False)
            new_result = None
    except SlackApiError as e:
        logger.exception(f"Error: {e}")
        raise e
    
    logger.append_keys(total_messages=len(conversation_history))
    return conversation_history

def not_signature_message(message):
    """
    A small check to determine if a given message in the slack conversation history a non signature message so it can be bypassed
    """
    return message.get("type", "") != "message" or message.get("subtype", "") != "bot_message"

def parse_message(message: Union[SlackMessage, dict], all_scanners: Dict[str, Scanner], all_signatures: Dict[str, Signature], non_valid_sigs: List[str] ):
    """
    parse_message takes a single message (SlackMessage or dict) and parses it for all necessary information.

    This updates the all_scanners Dictionary and the all_signatures Dictionary with the relavant objects
    """
    if type(message) is dict:
        message = SlackMessage(**message)

    for attachment in message.attachments:
        sig_name, sig_id, created = parse_attachement(attachment.title)
        scanner_name = attachment.author_name
        

        if sig_name is None:
            continue
        else:
            unique_sig_name = create_unique_sig_name(sig_name, sig_id)
            timestamp = message.ts

            if unique_sig_name in non_valid_sigs:
                continue

            group_id = parse_for_value_of("group_id", attachment.fallback)
            type_id = parse_for_value_of("type_id", attachment.fallback)
            description = parse_for_value_of("description", attachment.fallback)

            try:
                group = GroupID(int(group_id))
            except:
                group = GroupID.UNKNOWN

            if created and group in [GroupID.ORE]:
                # immediately filter out all new sigs that are Ore and hence not valid.
                logger.debug("Signature was an Ore on Creation - Ignoring", extra={"sig_name": sig_name, "sig_id": sig_id, "group_id": group_id, "type_id": type_id, "description": description})
                non_valid_sigs.append(unique_sig_name)
                continue

            elif created and group in [GroupID.COMBAT]:
                # Fitler out sigs that were just created and had a combat signature. 
                logger.debug("Signature was an Combat Sig on Creation - Ignoring", extra={"sig_name": sig_name, "sig_id": sig_id, "group_id": group_id, "type_id": type_id, "description": description})
                non_valid_sigs.append(unique_sig_name)
                continue
                
            update_scanner(all_scanners, scanner_name)
            update_signatures(all_scanners, all_signatures, sig_name, sig_id, scanner_name, unique_sig_name, timestamp, group_id, type_id, description)

                
    return 







    
