from datetime import date, datetime
import time

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


