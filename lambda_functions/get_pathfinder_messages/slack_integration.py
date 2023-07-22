
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from models.slack_messages import SlackMessage, Attachment
from models.scanner_data import Scanner, Signature
from typing import Union
from aws_lambda_powertools import Logger

logger = Logger()

import re

# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.


def slack_client_factory(token):
    return WebClient(token=token)


def get_channel(client, channel_name, conversation_id):

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
    if type(message) is dict:
        message = SlackMessage(**message)

    total_new_scanners = 0
    total_new_sigs = 0

    for attachment in message.attachments:
        sig_name, sig_id, created = parse_attachement(attachment.title)
        scanner_name = attachment.author_name
        

        if sig_name is None:
            continue
        else:
            unique_sig_name = f"{sig_name} ({sig_id})"
            timestamp = message.ts

            if unique_sig_name in non_valid_sigs:
                continue

            group_id = parse_for_value_of("group_id", attachment.fallback)
            type_id = parse_for_value_of("type_id", attachment.fallback)
            description = parse_for_value_of("description", attachment.fallback)

            if created and group_id in [None, "1", 1]:
                non_valid_sigs.append(unique_sig_name)
                continue

            if group_id in ["1", 1]:
                non_valid_sigs.append(unique_sig_name)
                continue
    
            

                
            total_new_scanners += update_scanner(all_scanners, scanner_name, unique_sig_name,)
            total_new_sigs += update_signatures(all_scanners, all_signatures, sig_name, sig_id, scanner_name, unique_sig_name, timestamp, group_id, type_id, description)
            
                
    return total_new_scanners, total_new_sigs

def update_signatures(all_scanners, all_signatures, sig_name, sig_id, scanner_name, unique_sig_name, timestamp, group_id, type_id, description):
    if unique_sig_name not in all_signatures.keys():
        sig = Signature(
                signature_name=sig_name,
                sig_id=sig_id,
                first_update_timestamp=float(timestamp),
                original_scanner_name=scanner_name,
                group_id=group_id,
                type_id=type_id,
                description=description
            )
        

        all_signatures[unique_sig_name] = sig
        all_scanners[scanner_name].scanner_credits(unique_sig_name, add=True)

        return 1

    else:

        all_signatures[unique_sig_name] = update_sig_if_older(all_scanners, scanner_name, unique_sig_name, timestamp, all_signatures[unique_sig_name])
        if group_id is not None:
            all_signatures[unique_sig_name].group_id = group_id
        if type_id is not None:
            all_signatures[unique_sig_name].type_id = type_id
        if description is not None:
            all_signatures[unique_sig_name].description = description
        
        return 0
    

def update_sig_if_older(all_scanners, scanner_name, unique_sig_name, timestamp, existing_sig):
    timestamp = float(timestamp)
    if timestamp < existing_sig.first_update_timestamp:
        original_scanner = existing_sig.original_scanner_name
        if original_scanner != scanner_name:
            all_scanners[scanner_name].scanner_credits(unique_sig_name, add=True)
            all_scanners[original_scanner].scanner_credits(unique_sig_name, add=False)
        existing_sig.first_update_timestamp = timestamp
    return existing_sig

def update_scanner(all_scanners, scanner_name, unique_sig_name):
    if scanner_name not in all_scanners.keys():
        scanner = Scanner(
                name=scanner_name,
                sigs_updated=[unique_sig_name],
                total_sigs=0
            )
        all_scanners[scanner_name] = scanner
        return 1
        
    else:
        return 0



            
        



def parse_attachement(title:str):

    sig_name, sig_id, created = extract_signature_and_id(title)

    if sig_name is None:
        return None, None, False
    
    return sig_name, sig_id, created
    

def parse_for_value_of(value_name:str, log_text: str):
    regex_dispatch = {
        # info type : [regex pattern, exceptions to return None]
        "group_id":  [r"groupId: (NULL|0) (➜|\\u279c) (\d)", [0, "0", 6, "6"] ],
        "type_id": [r"typeId: (NULL|0) (➜|\\u279c) (\d)", [0, "0"]],
        "description": [r"description: (NULL|0|\' \') (➜|\\u279c) '(.*)'", ["", " "]]
    }
    group_number = 3
    # if value_name not in regex_dispatch return None


    group_id_match = re.search(regex_dispatch[value_name][0], log_text)
    logger.debug(f"Parse for {value_name}", extra={"step": "created", "parsed_values": group_id_match, value_name: log_text})
    if group_id_match is None:
        return None
    elif group_id_match.group(group_number) in regex_dispatch[value_name][1]:
        logger.debug(f"Parse for {value_name}", extra={"step": "ignored values", value_name: group_id_match.group(group_number)})    
        return None
    else:
        return group_id_match.group(group_number)

    

def extract_signature_and_id(text):
    signature_update_pattern = r"^Updated signature '(\w{3}-\d{3})' (#\d*)$"

    match = re.search(signature_update_pattern, text)
    create = False
     
    if match is None:
        signature_create_pattern = r"^Created signature '(\w{3}-\d{3})' (#\d*)$"
        match = re.search(signature_create_pattern, text)
        create = True

    if match is None:
        return None, None, False
    
    return match.group(1), match.group(2), create
    
