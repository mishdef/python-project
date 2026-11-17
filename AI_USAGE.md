# AI Usage Disclosure

<!--
Fill in this file before you submit. Submissions without it are not graded.
If you used no AI tools, delete everything below and write only:
No AI tools were used.
-->

## Tools used

- Antigravity (Google DeepMind)

## Conversation links

- Link 1: In-IDE Antigravity session (Conversation ID: 7a9b2efe-e5e3-47de-bb8b-3d4798920bd2)

## What I used them for

- Asking how to properly detach and close Python logging handlers when running tests repeatedly in one process
- Clarifying regex edge cases for strict date-time string validation
- Checking how to handle custom usage error exit codes in argparse

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| `flight_parser.py` | `main` (logging cleanup) | Explained: asked why `test_main_twice_in_one_process` failed due to accumulated logging handlers, and Antigravity explained how to remove and close handlers inside `finally` |
| `validator.py` | `is_valid_datetime_format` | Explained: asked for advice on strictly enforcing `YYYY-MM-DD HH:MM` (exact 16 chars) before calling `strptime` |

## Key prompts

1. "Why does my FileHandler write duplicate lines when running unit tests that call main() multiple times in the same python process, and how should I clean it up?"
2. "What is the cleanest way in Python to strictly check that a datetime string is exactly in 'YYYY-MM-DD HH:MM' format and reject strings with invalid days or months?"

## What I changed or verified myself

- Implemented the entire `query.py` file completely on my own: wrote query validation logic (`is_valid_query`), all filtering criteria (`matches_query` with origin/destination exact matches, date inequalities, and price limits), sorting with `sort_by`/`order`, and the `limit` slicing.
- Implemented `csv_loader.py` completely on my own: reading files line-by-line with physical line numbering, stripping line endings, ignoring comments (`#`) and empty lines, skipping header row 1, using `csv.reader` on raw lines, formatting error strings (`<file>:<line>: <CODE> | <raw>`), and tracking duplicate flights across multiple files using a set of tuples.
- Implemented all 11 validation checks in `validator.py` in the required order, as well as `load_airports` and `to_record`.
- Implemented CLI argument validation, directory scanning (filtering `.csv` files and sorting them), input source mutual exclusion, and error handling in `flight_parser.py`.
- Ran the full public test suite (`python tests/run_public_tests.py`) repeatedly, verifying all 29 tests across grading groups A-H pass.
