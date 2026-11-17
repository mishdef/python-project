import csv
import os
from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    # parse given csv files in order and collect valid records + errors
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for p in paths:
        fname = os.path.basename(p)
        with open(p, "r", encoding="utf-8", newline="") as f:
            for line_no, line in enumerate(f, start=1):
                # header is line 1, skip it without validating
                if line_no == 1:
                    continue

                raw = line.rstrip("\r\n")
                s = line.strip()

                # skip empty lines
                if not s:
                    continue

                # skip comment lines starting with #
                if s.startswith("#"):
                    continue

                # split csv line into fields
                try:
                    rows = list(csv.reader([raw]))
                    fields = rows[0] if rows else []
                except Exception:
                    fields = []

                # validate fields (checks 1-11)
                err = validate_row(fields, airports)
                if err is not None:
                    errors.append(f"{fname}:{line_no}: {err} | {raw}")
                    continue

                # check for duplicate flight (check 12)
                rec = to_record(fields)
                key = (rec["flight_id"], rec["departure_datetime"])
                if key in seen:
                    errors.append(f"{fname}:{line_no}: DUPLICATE_FLIGHT | {raw}")
                    continue

                seen.add(key)
                records.append(rec)

    return records, errors
