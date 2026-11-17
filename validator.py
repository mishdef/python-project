import re
import math
from datetime import datetime


def load_airports(path: str) -> set[str]:
    # load airport codes from file into a set
    codes = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            # ignore empty lines or comments
            if not s or s.startswith("#"):
                continue
            codes.add(s)
    return codes


def is_valid_datetime_format(val: str) -> bool:
    # check string length and strict format: YYYY-MM-DD HH:MM
    if not isinstance(val, str) or len(val) != 16:
        return False
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", val):
        return False
    # check if calendar date and time actually exist
    try:
        datetime.strptime(val, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    # check 1: row must have exactly 6 columns
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    # trim spaces from all values
    row = [x.strip() for x in fields]
    flight_id, origin, dest, dep, arr, price = row

    # check 2: none of the fields can be empty
    if any(x == "" for x in row):
        return "MISSING_FIELD"

    # check 3: flight id is 2 to 8 alphanumeric characters
    if not re.fullmatch(r"[A-Za-z0-9]{2,8}", flight_id):
        return "INVALID_FLIGHT_ID"

    # check 4: origin must be 3 uppercase letters and exist in airports set
    if not (re.fullmatch(r"[A-Z]{3}", origin) and origin in airports):
        return "INVALID_ORIGIN"

    # check 5: destination must be 3 uppercase letters and exist in airports set
    if not (re.fullmatch(r"[A-Z]{3}", dest) and dest in airports):
        return "INVALID_DESTINATION"

    # check 6: origin and destination cannot be identical
    if origin == dest:
        return "SAME_ORIGIN_DESTINATION"

    # check 7: departure datetime format
    if not is_valid_datetime_format(dep):
        return "INVALID_DEPARTURE"

    # check 8: arrival datetime format
    if not is_valid_datetime_format(arr):
        return "INVALID_ARRIVAL"

    # check 9: arrival must be strictly after departure
    t1 = datetime.strptime(dep, "%Y-%m-%d %H:%M")
    t2 = datetime.strptime(arr, "%Y-%m-%d %H:%M")
    if t2 <= t1:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # check 10: price must be a valid finite float
    try:
        p = float(price)
        if not math.isfinite(p):
            return "INVALID_PRICE"
    except (ValueError, TypeError):
        return "INVALID_PRICE"

    # check 11: price must be greater than zero
    if p <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    # convert cleaned row to record dict
    row = [x.strip() for x in fields]
    return {
        "flight_id": row[0],
        "origin": row[1],
        "destination": row[2],
        "departure_datetime": row[3],
        "arrival_datetime": row[4],
        "price": float(row[5]),
    }
