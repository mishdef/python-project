import math
from validator import is_valid_datetime_format

# valid keys that can appear in query
ALLOWED_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
    "min_price",
    "sort_by",
    "order",
    "limit",
}

# fields available in flight record
RECORD_FIELDS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}


def is_valid_query(query: dict) -> bool:
    # check that query is a dict and has only allowed keys
    if not isinstance(query, dict):
        return False

    for k in query:
        if k not in ALLOWED_KEYS:
            return False

    # order requires sort_by, and can only be asc or desc
    if "order" in query:
        if "sort_by" not in query:
            return False
        if query["order"] not in ("asc", "desc"):
            return False

    # sort_by must be one of the flight record fields
    if "sort_by" in query:
        if query["sort_by"] not in RECORD_FIELDS:
            return False

    # string fields must be strings
    for k in ("flight_id", "origin", "destination"):
        if k in query and not isinstance(query[k], str):
            return False

    # datetime fields must match format YYYY-MM-DD HH:MM
    for k in ("departure_datetime", "arrival_datetime"):
        if k in query:
            val = query[k]
            if not isinstance(val, str) or not is_valid_datetime_format(val):
                return False

    # price and min_price: numbers only, booleans not allowed, must be finite
    for k in ("price", "min_price"):
        if k in query:
            val = query[k]
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                return False

    # limit must be integer >= 0 (and not bool)
    if "limit" in query:
        val = query["limit"]
        if isinstance(val, bool) or not isinstance(val, int) or val < 0:
            return False

    return True


def matches_query(flight: dict, query: dict) -> bool:
    # exact string matching
    for field in ("flight_id", "origin", "destination"):
        if field in query and flight.get(field) != query[field]:
            return False

    # departure: at or after specified time
    if "departure_datetime" in query:
        if flight["departure_datetime"] < query["departure_datetime"]:
            return False

    # arrival: at or before specified time
    if "arrival_datetime" in query:
        if flight["arrival_datetime"] > query["arrival_datetime"]:
            return False

    # price: at most max price
    if "price" in query:
        if flight["price"] > query["price"]:
            return False

    # min_price: at least min price
    if "min_price" in query:
        if flight["price"] < query["min_price"]:
            return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    # check query validity
    if not is_valid_query(query):
        return {
            "query": query,
            "error": "INVALID_QUERY",
            "matches": [],
        }

    # filter database records
    matches = [f for f in db if matches_query(f, query)]

    # sort if requested
    if "sort_by" in query:
        k = query["sort_by"]
        rev = query.get("order", "asc") == "desc"
        matches = sorted(matches, key=lambda x: x[k], reverse=rev)

    # apply limit
    if "limit" in query:
        matches = matches[:query["limit"]]

    return {
        "query": query,
        "matches": matches,
    }


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    # wrap single query into list if needed
    q_list = queries if isinstance(queries, list) else [queries]
    return [run_query(db, q) for q in q_list]
