import argparse
import input
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from solve import Premise

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

class Step:
    def __init__(self, premise: 'Premise', type: str):
        self.premise = premise
        self.type = type


class NaturalDeductionTree:
    def __init__(self):
        self.steps: list[Step] = []

    def add(self, step: Step):
        self.steps.append(step)
    