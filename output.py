import argparse
import input

def display_start() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file", help="Parse from a file")
    p.add_argument("--debug", help="Enable debuggin")
    args = p.parse_args()

    if args.file:
        print(f"Importing statements from {args.file}...\n")
        input.read_from_file(args.file)
    else:
        input.read_from_input()
    