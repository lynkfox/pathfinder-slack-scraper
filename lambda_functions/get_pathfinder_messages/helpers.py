from datetime import date, datetime
from aws_lambda_powertools import Logger
import re
import time

logger = Logger()



def build_combat_signature_regex():

    pirate_names = ["Angel", "Blood", "Blood Raider", "Gurista", "Guristas", "Sansha", "Serpentis"]

    suffix = ["Hideout", "Lookout", "Watch", "Vigil", "Outpost", "Annex", "Base", "Fortress", "Military Complex", "Provincial HQ", "Fleet Staging Point", "Domination Fleet Staging Point"]

    return rf"({'|'.join(pirate_names)}) ({'|'.join(suffix)})"

PIRATE_SITE_REGEX = build_combat_signature_regex()

def get_week_start_end_datetimes(year: int=0, week:int=0):
    """
    Provides the datetimes for the start of the week through the start of nextweek 
    (Midnight Monday-the following monday midnight)
    
    Defaults to the current week.

    Can pass negative week numbers to get that many weaks ago. Ie -1 for last week
    """
    this_week = date.today().isocalendar()

    modifier = None

    if type(week) is str:
        if week[0] == "-" or week[0] == "+":
            modifier = int(week)
        else:
            week = int(week)

    if type(week) is int and week < 0:
        modifier = week
    
    
    if year is None or (year > 2999 or year < 2023):
        year = this_week.year

    if modifier is None and (week is None or (week > 52 or week < 0)):
        week = this_week.week
    elif modifier:
        week = this_week.week+modifier

    if week is None:
        week = this_week.week


    start_of_week = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{year}-W{week+1}-1", "%Y-W%W-%w")

    return start_of_week, end_of_week

def convert_week_bookends_to_timestamps(start_of_week, end_of_week):

    end_timestamp = time.mktime(end_of_week.timetuple())
    start_timestamp = time.mktime(start_of_week.timetuple())
    return start_timestamp, end_timestamp



def check_if_combat_signature(description):
    drone_names = ["Haunted Yard", "Desolate Site", "Chemical Yard", "Rogue Trial Yard", "Dirty Site", "Ruins", "Independence", "Radiance"]

    if description in drone_names or re.search(PIRATE_SITE_REGEX) is not None:
        return True
    
    return False
    


            
        
def create_unique_sig_name(sig_name, sig_id):
    return f"{sig_name} ({sig_id})"


def parse_attachement(title:str):

    sig_name, sig_id, created = extract_signature_and_id(title)

    if sig_name is None:
        return None, None, False
    
    return sig_name, sig_id, created
    

def parse_for_value_of(value_name:str, log_text: str):
    regex_dispatch = {
        # info type : [regex pattern, exceptions to return None]
        "group_id":  [r"groupId: (NULL|0) (➜|\\u279c) (\d)", [0, "0"] ],
        "type_id": [r"typeId: (NULL|0) (➜|\\u279c) (\d)", [0, "0"]],
        "description": [r"description: (NULL|0|\' \') (➜|\\u279c) '(.*)'", ["", " "]]
    }
    regex_group_number = 3
    # if value_name not in regex_dispatch return None


    matches = re.search(regex_dispatch[value_name][0], log_text)
    logger.debug(f"Parse for {value_name}", extra={"step": "created", "parsed_values": matches, value_name: log_text})
    if matches is None:
        return None
    elif matches.group(regex_group_number) in regex_dispatch[value_name][1]:
        logger.debug(f"Parse for {value_name}", extra={"step": "ignored values", value_name: matches.group(regex_group_number)})    
        return None
    else:
        return matches.group(regex_group_number)
    

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