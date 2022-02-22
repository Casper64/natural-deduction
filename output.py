import argparse
from enum import Enum
from random import random
import re
import input
import debug
import math
import util
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from solve import Premise

def display_start() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file", help="Parse from a file")
    p.add_argument("--debug", help="Enable debuggin", action='store_true')
    args = p.parse_args()

    if args.file:
        print(f"Importing statements from {args.file}...\n")
        input.read_from_file(args.file)
    else:
        input.read_from_input()

    if args.debug:
        debug.DEBUG = True


class StepType(Enum):
    P=0 # Premise
    A=1 # Assumption
    OA=2 # Open Assumption
    CA=3 # Close Assumption
    EI=4 # Elimination implication
    II=5 # Introdcution implication
    CT=6 # Contradiction aka Introduction negation
    IN=7 # Introduction negation
    EN=8 # Elimination negation
    IA=9 # Introduction and
    EA=10 # Elimination and
    RI=11 # Reiteration

class Step:
    # TODO: implement rule numbers for the steps, hashmap maybe??
    def __init__(self, premise: 'Premise', type: StepType, assumptions: list['Premise']=None):
        self._premise = premise
        premise = str(premise).replace("[", "(").replace("]", ")").replace("'", "")
        self.premise = premise
        self._type = type
        self._assumptions = assumptions

    def get(self):
        if self._type == StepType.P:
            return "[ass.]"
        elif self._type == StepType.A:
            return "[ass.]"
        elif self._type == StepType.EI:
            return "[E→, "
        elif self._type == StepType.II:
            return "[I→, "
        elif self._type == StepType.CT:
            return "[I¬, "
        elif self._type == StepType.IN:
            return "[I¬, "
        elif self._type == StepType.EN:
            return "[E¬, " 
        elif self._type == StepType.IA:
            return "[I^, "
        elif self._type == StepType.EA:
            return "[E^, "
        elif self._type == StepType.RI:
            return f"[reit.,#{self._premise.id}]"

        return self._type
    def __repr__(self):
        return f"{self.premise} {self.get()}"


class NaturalDeductionTree:
    def __init__(self, statement: str):
        self.steps: list[Step] = []
        self.statement = statement.replace(":-", "⊢")
        self.statement = statement.replace("!", "¬")

    def add(self, step: Step):
        self.steps.append(step)

    def get_premise(self, id: int, r: list[(str, 'Premise')]) -> 'Premise':
        for i, (_, a) in enumerate(r):
            print(a.id, id)
            if a.id == id:
                return i

    def close(self):
        result: list[(str, 'Premise')] = []
        r = str(random())
        level = 1
        line = 1
        max_lines = len(str(len(self.steps)))
        max_prepend = ' ' * max_lines

        for i, step in enumerate(self.steps):
            # Change current level if open assumption or close assumption
            if step._type == StepType.OA:
                level += 1
                continue
            elif step._type == StepType.CA:
                level -= 1
                continue
            
            lines = f"{line}{' ' * (max_lines - len(str(line)))}"

            if isinstance(step.premise, str):
                premise = util.raw_to_str(step.premise)
            else:
                premise = util.cleanup(str(step.premise))

            premise = premise.replace("!", "¬")

            if step._type == StepType.CT:
                premise = "⊥"

            raw_step = step.get()
            while match := re.search(r"#(\d+)", raw_step):
                id = match.group(1)
                i = self.get_premise(int(id), result)
                raw_step = raw_step[:match.start()]+str(i+1)+raw_step[match.end():]
                break

            string = f"{lines}{' │ ' * level}{premise}{r}_{raw_step}\n"

            # Open assumption so draw a line
            if step._type == StepType.A and i-1 >= 0 and self.steps[i-1]._type == StepType.OA:
                string += f"{max_prepend}{' │ ' * (level-1)} ├{'─'*len(premise)}\n"
            # If its the last premise draw a line
            elif step._type == StepType.P and i+1 != len(self.steps) and self.steps[i+1]._type != StepType.P:
                string += f"{max_prepend}{' │ ' * (level-1)} ├{'─'*(len(premise)+1)}\n"
            # If its the last premise draw a line, but added the case where the premise is the last premise
            elif step._type == StepType.P and i+1 == len(self.steps):
                string += f"{max_prepend}{' │ ' * (level-1)} ├{'─'*(len(premise)+1)}\n"


            result.append((string, step._premise))
            line += 1


        max_len = max([len(x[0].split("\n")[0]) for x in result])

        p = self.statement+"\n\n"

        for string, premise in result:
            s = string.split("\n")[0]
            l = len(s)
            l2 = len(s.split("_")[1])
            # Align all action type thingies to the right on the same place
            replaceable = " " * (4 + max_len - l + l2)
            string = string.replace(r+"_", replaceable)
            p += string

        # TODO: better way of printing?
        print(p)