"""Run duplicate request demonstrations locally; never calls AWS."""
import argparse
import json
from .requests import submit_request, list_records

def main():
    parser = argparse.ArgumentParser(description="CloudLaunch request prototype")
    parser.add_argument("command", choices=["submit", "list"])
    parser.add_argument("--db", default="cloudlaunch_demo.sqlite3")
    parser.add_argument("--file", help="JSON request file (submit only)")
    parser.add_argument("--key", help="Unique submission token (submit only)")
    args = parser.parse_args()
    if args.command == "submit":
        if not args.file or not args.key:
            parser.error("submit requires --file and --key")
        with open(args.file, encoding="utf-8") as stream:
            result = submit_request(args.db, json.load(stream), args.key)
    else:
        result = list_records(args.db)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
