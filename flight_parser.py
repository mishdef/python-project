import argparse
import json
import logging
import os
import sys
from datetime import datetime

from validator import load_airports
from csv_loader import parse_files
from query import run_queries

STUDENT_ID = "260ADB168"
FIRST_NAME = "Mykhailo"
LAST_NAME = "Stadnikov"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Flight Schedule Parser and Query Tool",
    )
    # data source options (must specify exactly one)
    p.add_argument("-i", "--input", dest="input", help="Parse single CSV file")
    p.add_argument("-d", "--directory", dest="directory", help="Parse all CSV files in folder")
    p.add_argument("-j", "--jsondb", dest="jsondb", help="Load existing JSON database")

    # additional options
    p.add_argument("-a", "--airports", dest="airports", help="Airport list file")
    p.add_argument("-o", "--output", dest="output", default=None, help="Output path for JSON database")
    p.add_argument("-q", "--query", dest="query", help="Path to queries JSON file")
    p.add_argument("-r", "--response-dir", dest="response_dir", default=".", help="Folder for query responses")

    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # parse arguments (returns code 2 on usage/syntax error)
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code)

    # check data source rules (exit code 2 on conflict or missing source)
    sources = [args.input is not None, args.directory is not None, args.jsondb is not None]
    if sum(sources) == 0:
        try:
            parser.error("Must specify exactly one data source: -i, -d, or -j")
        except SystemExit as e:
            return int(e.code)

    if sum(sources) > 1:
        try:
            parser.error("Multiple data sources specified; choose only one of -i, -d, or -j")
        except SystemExit as e:
            return int(e.code)

    if (args.input is not None or args.directory is not None) and not args.airports:
        try:
            parser.error("-a is required with -i or -d")
        except SystemExit as e:
            return int(e.code)

    if args.jsondb is not None and args.output is not None:
        try:
            parser.error("-o is not allowed with -j")
        except SystemExit as e:
            return int(e.code)

    # runtime checks (exit code 1, print error message to stderr)
    try:
        # validate query file if provided
        query_data = None
        if args.query is not None:
            if not os.path.isfile(args.query):
                sys.stderr.write(f"Error: Query file not found: {args.query}\n")
                return 1
            try:
                with open(args.query, "r", encoding="utf-8") as f:
                    query_data = json.load(f)
            except Exception as e:
                sys.stderr.write(f"Error: Query file is not valid JSON: {e}\n")
                return 1

            # query file must be dict or list of dicts
            if not (isinstance(query_data, dict) or (isinstance(query_data, list) and all(isinstance(x, dict) for x in query_data))):
                sys.stderr.write("Error: Query file must contain an object or an array of objects\n")
                return 1

            if not os.path.isdir(args.response_dir):
                sys.stderr.write(f"Error: Response folder does not exist: {args.response_dir}\n")
                return 1

        # case A: load existing json database (-j)
        if args.jsondb is not None:
            if not os.path.isfile(args.jsondb):
                sys.stderr.write(f"Error: JSON database file not found: {args.jsondb}\n")
                return 1
            try:
                with open(args.jsondb, "r", encoding="utf-8") as f:
                    db_records = json.load(f)
            except Exception as e:
                sys.stderr.write(f"Error: Database is not valid JSON: {e}\n")
                return 1

            if not isinstance(db_records, list):
                sys.stderr.write("Error: Database must be a JSON array\n")
                return 1

            # run queries if requested
            if args.query is not None:
                responses = run_queries(db_records, query_data)
                now_str = datetime.now().strftime("%Y%m%d_%H%M")
                out_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{now_str}.json"
                out_path = os.path.join(args.response_dir, out_name)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(responses, f, indent=2)

            return 0

        # case B: parse csv input (-i or -d)
        if not os.path.isfile(args.airports):
            sys.stderr.write(f"Error: Airports file not found: {args.airports}\n")
            return 1

        try:
            airports = load_airports(args.airports)
        except Exception as e:
            sys.stderr.write(f"Error: Failed to read airports file: {e}\n")
            return 1

        # collect files to parse
        csv_files = []
        if args.input is not None:
            if not os.path.isfile(args.input):
                sys.stderr.write(f"Error: CSV file not found: {args.input}\n")
                return 1
            csv_files = [args.input]
        elif args.directory is not None:
            if not os.path.isdir(args.directory):
                sys.stderr.write(f"Error: Directory not found: {args.directory}\n")
                return 1
            try:
                names = sorted(os.listdir(args.directory))
            except Exception as e:
                sys.stderr.write(f"Error: Cannot read directory: {e}\n")
                return 1

            csv_files = [
                os.path.join(args.directory, name)
                for name in names
                if name.endswith(".csv") and os.path.isfile(os.path.join(args.directory, name))
            ]
            if not csv_files:
                sys.stderr.write(f"Error: No .csv files found in directory: {args.directory}\n")
                return 1

        # determine db output and log output paths
        db_path = args.output if args.output is not None else "db.json"
        out_dir = os.path.dirname(db_path)
        if out_dir and not os.path.isdir(out_dir):
            sys.stderr.write(f"Error: Output folder does not exist: {out_dir}\n")
            return 1

        log_path = os.path.join(out_dir, "errors.log") if out_dir else "errors.log"

        # setup logging to errors.log
        logger = logging.getLogger("flight_parser")
        logger.setLevel(logging.INFO)
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()

        handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)

        try:
            records, errors = parse_files(csv_files, airports)
            for err in errors:
                logger.warning(err)

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        finally:
            # clean up handler so repeat runs don't duplicate logs
            logger.removeHandler(handler)
            handler.close()

        # run queries if requested
        if args.query is not None:
            responses = run_queries(records, query_data)
            now_str = datetime.now().strftime("%Y%m%d_%H%M")
            out_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{now_str}.json"
            out_path = os.path.join(args.response_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(responses, f, indent=2)

        return 0

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
