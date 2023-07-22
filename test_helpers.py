import pytest
from freezegun import freeze_time
from datetime import date, datetime

from lambda_functions.get_pathfinder_messages.helpers import get_week_start_end_datetimes

@freeze_time("2023-06-06")
def test_get_week_start_end_times_with_none():
    start_of_week = datetime.strptime(f"{2023}-W{23}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{24}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week=None)

    assert result == (start_of_week, end_of_week)

@freeze_time("2023-06-06")
def test_get_week_start_end_times_with_negative_string_week_value():

    start_of_week = datetime.strptime(f"{2023}-W{18}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{19}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week="-5")

    assert result == (start_of_week, end_of_week)

@freeze_time("2023-06-06")
def test_get_week_start_end_times_with_positive_string_week_value():

    start_of_week = datetime.strptime(f"{2023}-W{26}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{27}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week="+3")

    assert result == (start_of_week, end_of_week)

@freeze_time("2023-06-06")
def test_get_week_start_end_times_with_negative_int_week_value():

    this_week = date.today().isocalendar()
    start_of_week = datetime.strptime(f"{2023}-W{18}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{19}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week=-5)

    assert result == (start_of_week, end_of_week)

@freeze_time("2023-06-06")
def test_get_week_start_end_times_with_positive_int_picks_that_week():

    start_of_week = datetime.strptime(f"{2023}-W{3}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{4}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week=3)

    assert result == (start_of_week, end_of_week)

@freeze_time("2023-01-04")
def test_get_week_start_end_times_when_week_is_currently_1_and_neg_numbers():

    start_of_week = datetime.strptime(f"{2022}-W{52}-1", "%Y-W%W-%w")
    end_of_week = datetime.strptime(f"{2023}-W{1}-1", "%Y-W%W-%w")

    result = get_week_start_end_datetimes(year=None, week=-1)

    assert result == (start_of_week, end_of_week)