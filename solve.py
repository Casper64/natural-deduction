from tokens import Token
from typing import Union
from xml.dom.expatbuilder import Rejecter
import debug
from parse import Parser
from ruler import Ruler
import input
import re
import util
from  rules_core.negation import negate
from output import NaturalDeductionTree, StepW

CONCLUDE = ":-"

def init():
    for statement in input.statements:
        debug.log(f"Current statement: '{statement}'")
        solver = Solver(statement)
        solver.start()
        if solver.solved:
            debug.log(f"Found solution!\n", debug.SUCCESS)
        else:
            debug.log(f"Solution not found!\n", debug.ERROR)

class Premise:
    def __init__(self, premise: str, raw=None):
        self._premise = util.cleanup(premise)
        self._parse()

    def get(self):
        return self._premise

    def set(self, premise: str):
        self._premise = premise
        self._parse()

    def duplicate(self, premise: str):
        return Premise(premise)

    def _parse(self, raw=None):
        parser = Parser(self._premise, raw)
        self.raw = parser.raw
        self.literals = parser.literals
        self.tokens = parser.tokens

    def from_raw(raw: list):
        """Returns premise created from raw state"""
        string = str(raw).replace("[", "(").replace("]", ")").replace("'", "").replace(",", "")
        return Premise(string, raw)

    def __eq__(self, other: any):
        if isinstance(other, str):
            return self._premise == other
        elif isinstance(other, list):
            return str(self.raw) == str(other)
        elif isinstance(other, Premise):
            return str(self.raw) == str(other.raw)

    def __ne__(self, other: any):
        if isinstance(other, str):
            return self._premise != other
        elif isinstance(other, list):
            return str(self.raw) != str(other)
        elif isinstance(other, Premise):
            return self._premise != other._premise

    def __repr__(self):
        return f"{self._premise}"

class Layer:
    def __init__(self, proved: list[Premise], assumption: Premise):
        self.assumption = assumption
        # In the layer itself the assumption is considered proved, but we know that might not be the case
        # So we have to keep track of it
        self.proved = proved
        if assumption:
            self.proved.append(assumption)

    def __repr__(self):
        return f"Assumption = {self.assumption}"


class Solver:
    def __init__(self, statement: str):
        self.solved = False

        self.statement = statement
        a = statement.split(CONCLUDE)
        if len(a) < 2:
            raise Exception("Statement does include a conclusion")
        elif len(a) > 2:
            raise Exception("Statement includes multiple conclusions")
        
        debug.log(f"Parsing '{statement}'")

        self.premises = [Premise(x) for x in a[0].split(",")]
        self.conclusion = Premise(a[1])
        debug.log(f"Raw representation of conclusion {self.conclusion.raw}")
        debug.log(f"With tokens = {self.conclusion.tokens}")

        if not self.conclusion.get():
            debug.log("No conclusion is found", debug.ERROR)
            raise Exception("A conclusion must be provided")
        else:
            debug.log("Found valid premise(s) and conclusion", debug.SUCCESS)

        self.ruler = Ruler()

        self.stack: list[Layer] = []
        self.level = 0
        self.stack.append(Layer(self.premises, []))

    def start(self):
        debug.log("Starting solver")
        return self.prove(self.conclusion)

    def prove(self, target: Premise):
        debug.log(f"Trying to prove {target}")
        token = target.tokens.get_main_operator()

        # If the target to prove has an operator in it we need to somehow prove that the
        # introduction rule of that operator is applicable in the current state.
        # If not then the target is a contradiction
        if token:
            result = self.ruler.introduce(token.operator)(self, target.tokens, token)
            print(result)
        else:
            debug.log(f"No operator found so target must be a literal")
            
            # Checking if the target is already proved or the target is a contradiction
            neg = negate(target)
            for premise in self.stack[self.level].proved:
                if premise == target:
                    debug.log(f"{target} is already proved!")
                    self.resolve(target)
                    return True
                if premise == neg:
                    debug.log(f"Can't prove {target} because it contradicts with {premise}")
                    self.reject(target)
                    return False

            # Get all the premises where the literal is used
            valids: list[Premise] = []
            for premise in self.stack[-1].proved:
                t = target.get().replace("!","")
                for literal in premise.literals:
                    if re.match(r"!?"+t, literal):
                        valids.append(premise)
                        break

            debug.log(f"Valid premises containing literal {target} = {valids}")
            for premise in valids:
                found = self.extract(premise, target)
                if found:
                    self.resolve(target)
                    return True

            return False

    def extract(self, premise: Premise, target: Premise):
        debug.log(f"Trying to extract {target} from {premise}")
        token = premise.tokens.get_main_operator()

        # If there is no operator in the premise the premise is a literal
        if not token:
            debug.log(f"No operator found so premise must be a literal. You should not use 'Solver.extract' for comparing a literal with a literal", debug.WARNING)
            return premise == target

        return self.ruler.eliminate(token.operator)(self, premise.tokens, token)
        

    def resolve(self, premise: Premise):
        debug.log(f"{premise} is true!")
        if self.level == 0:
            self.solved = True
            return True

        # Make all the assumptions made at the previous layer true or somethign idk
        # Maybe only for all introduction rules 

        previous = self.stack.pop()
        self.level -= 1
        debug.log(f"Layer popped. New layer at level {self.level}: {self.stack[self.level]}")
        return True

    def reject(self, premise: Premise):
        debug.log(f"{premise} is false!")
        if self.level == 0:
            self.solved = True
            return True

        previous = self.stack.pop()
        self.level -= 1
        debug.log(f"Layer popped. New layer at level {self.level}: {self.stack[self.level]}")
        return True

    def assume(self, token: Token):
        premise = Premise.from_raw(token)
        self.stack.append(Layer(self.stack[self.level].proved, premise))
        self.level += 1

        debug.log(f"New layer created at level {self.level}: {self.stack[self.level]}")
        return premise

    def add_prove(self, premise):
        if isinstance(premise, Premise):
            self.stack[self.level].proved.append(premise)
        elif isinstance(premise, list):
            p = Premise.from_raw(premise)
            self.stack[self.level].proved.append(p)
        elif isinstance(premise, str):
            p = Premise(premise)
            self.stack[self.level].proved.append(p)
        elif isinstance(premise, Token):
            p = Premise.from_raw(premise.raw())
            self.stack[self.level].proved.append(p)