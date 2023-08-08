
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from models.slack_messages import SlackMessage
from models.scanner_data import Scanner, Signature, GroupID
from typing import Union
from aws_lambda_powertools import Logger
from helpers import parse_attachement, create_unique_sig_name, parse_for_value_of

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


def get_messages(conversation_id, client, start_timestamp, end_timestamp):
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


def parse_message(message: Union[SlackMessage, dict], all_scanners, all_signatures, non_valid_sigs):
    """
    parse_message takes a single message (SlackMessage or dict) and parses it for all necessary information.
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



def update_signatures(all_scanners, all_signatures, sig_name, sig_id, scanner_name, unique_sig_name, timestamp, group_id, type_id, description):
    """
    update_signatures will take the values extracted from a message and either create the signature if it does not exist or update an existing one with new values.

    it will also update the scanner involved if it is a new signature, and if it is an existing signature it will update scanners if the message timestamp is earlier than
    the currently recorded one.
    """
    if unique_sig_name not in all_signatures.keys():
        sig = Signature(
                name=sig_name,
                id=sig_id,
                first_update_timestamp=timestamp,
                original_scanner_name=scanner_name,
                group_id=group_id,
                type_id=type_id,
                description=description
            )
        

        all_signatures[unique_sig_name] = sig
        all_scanners[scanner_name].scanner_credits(sig, add=True)
        

    else:

        all_signatures[unique_sig_name] = update_sig_if_older(all_scanners, scanner_name, timestamp, all_signatures[unique_sig_name])
        if group_id is not None:
            all_signatures[unique_sig_name].group_id = group_id
        if type_id is not None:
            all_signatures[unique_sig_name].type_id = type_id
        if description is not None:
            all_signatures[unique_sig_name].description = description
        
        sig = all_signatures[unique_sig_name]

    logger.debug(f"{unique_sig_name} Updated", extra=sig.model_dump(mode="JSON"))
    return sig
    

def update_sig_if_older(all_scanners, scanner_name, timestamp, existing_sig):
    """
    update_sig_if_older checks to see if the signature that is already recorded as a scanner credit, if its timestamp is newer than the message being parsed.
    if so, the scanner credit is updated.
    """
    if timestamp < existing_sig.first_update_timestamp:
        original_scanner = existing_sig.original_scanner_name
        if original_scanner != scanner_name:
            all_scanners[scanner_name].scanner_credits(existing_sig, add=True)
            all_scanners[original_scanner].scanner_credits(existing_sig, add=False)
        existing_sig.first_update_timestamp = timestamp
    return existing_sig

def update_scanner(all_scanners, scanner_name):
    if scanner_name not in all_scanners.keys():
        scanner = Scanner(
                name=scanner_name,
                sigs_updated=[],
                total_sigs=0,
                valid_sig_audit = [],
                non_valid_sig_audit = []
            )
        all_scanners[scanner_name] = scanner
        return
        
    else:
        return



    
