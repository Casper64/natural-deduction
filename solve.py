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
from output import NaturalDeductionTree, Step, StepType

# TODO: Add docstrings to all methods!!

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
        solver.nd.close()

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
        elif isinstance(other, Token):
            return str(self) == str(other)

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
    def __init__(self, proved: list[Premise], assumption: Premise, target: Premise):
        self.assumption = assumption
        self.target = target
        # In the layer itself the assumption is considered proved, but we know that might not be the case
        # So we have to keep track of it
        self.proved = proved
        if assumption:
            self.proved.append(assumption)
            

    def __repr__(self):
        return f"Assumption = {self.assumption}, proved = {self.proved}"


class Solver:
    def __init__(self, statement: str):
        self.solved = False
        self.nd = NaturalDeductionTree(statement)

        self.statement = statement
        a = statement.split(CONCLUDE)
        if len(a) < 2:
            raise Exception("Statement does include a conclusion")
        elif len(a) > 2:
            raise Exception("Statement includes multiple conclusions")
        
        debug.log(f"Parsing '{statement}'")

        self.premises = [Premise(x) for x in a[0].split(",")]
        self.conclusion = Premise(a[1])
        
        for premise in self.premises:
            self.nd.add(Step(premise, StepType.P))

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
        self.stack.append(Layer(self.premises, [], self.conclusion))

    def start(self):
        debug.log("Starting solver")
        result = self.prove(self.conclusion)
        if not result:
            self.nd.add(Step("", StepType.CT))
            return False
        self.solved = result
        return result

    def prove(self, target: Premise, caller: StepType = None):
        if not isinstance(target, Premise):
            target = Premise.from_raw(target)

        debug.log(f"Trying to prove {target}")
        token = target.tokens.get_main_operator()

        # If the target to prove has an operator in it we need to somehow prove that the
        # introduction rule of that operator is applicable in the current state.
        # If not then the target is a contradiction
        if token:
            result = self.ruler.introduce(token.operator)(self, target.tokens, token)
            if result:
                # return self.resolve(target)
                if target == self.stack[self.level].target:
                        return self.resolve(target)
                else:
                    return True
            return self.reject(target)
        else:
            debug.log(f"No operator found so target must be a literal")
            
            # Checking if the target is already proved or the target is a contradiction
            neg = negate(target)
            for premise in self.stack[self.level].proved:
                if premise == target:
                    debug.log(f"{target} is already proved!")
                    if target == self.stack[self.level].target:
                            self.resolve(target)
                    return True
                if premise == neg:
                    # Prove target with rule of called?
                    if not caller:
                        self.add_prove(target)
                    debug.log(f"Can't prove {target} because it contradicts with {premise}")
                    
                    return False

            # Get all the premises where the literal is used
            valids: list[Premise] = []


            for premise in self.stack[-1].proved:
                t = target.get().replace("!","")
                for literal in premise.literals:
                    if re.match(r"!?"+t, literal):
                        l = Premise(literal)
                        valids.append((l, premise))
                        break

            # If there are no valids the premise can't be proved
            if len(valids) == 0:
                debug.log(f"No valid premises were found trying to prove {target}")
                return False

            debug.log(f"Valid premises containing literal {target} = {valids}")
            for t, premise in valids:
                found = self.extract(premise, t)
                if found:
                    # Check if the extraction succeeded, but not yet found the right target
                    if target in self.stack[self.level].proved:
                        self.resolve(target)
                        continue
                    # Else remove the prove because the target was not found and we need to continue
                    # Maybe this crashes at some point because a next prove on the same level needs the premise
                    else:
                        debug.log(f"(see below) because {target} was not found, but something else did. semi fix? (from 'solve.py:192')", debug.WARNING)
                self.remove_prove(premise)

            return self.prove(self.stack[self.level].target)

    def extract(self, premise: Premise, target: Premise):
        debug.log(f"Trying to extract {target} from {premise}")
        token = premise.tokens.get_main_operator()

        # If there is no operator in the premise the premise is a literal
        if not token:
            debug.log(f"No operator found so premise must be a literal. You should not use 'Solver.extract' for comparing a literal with a literal", debug.WARNING)
            return premise == target
        
        return self.ruler.apply(token.operator)(self, target, premise.tokens, token)

    def resolve(self, premise: Premise):
        debug.log(f"{premise} is true!")
        self.nd.add(Step("", StepType.CA))
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
        self.nd.add(Step("", StepType.CT))
        self.nd.add(Step("", StepType.CA))

        if self.level == 0:
            self.solved = False
            return False

        previous = self.stack.pop()
        debug.log(f"{previous.assumption} is false!")
        self.level -= 1
        self.stack[self.level].proved.remove(previous.assumption)


        neg = negate(previous.assumption)
        self.add_prove(neg, False)
        if premise in self.stack[self.level].proved:
            self.stack[self.level].proved.remove(premise)
        self.nd.add(Step(neg, StepType.EN))


        debug.log(f"Layer popped. New layer at level {self.level}: {self.stack[self.level]}")

        return False

    def assume(self, token: Token, target: Token):
        premise = Premise.from_raw(token)
        pt = Premise.from_raw(target)
        self.nd.add(Step("", StepType.OA))
        self.nd.add(Step(premise, StepType.A))
        self.stack.append(Layer(self.stack[self.level].proved, premise, pt))
        self.level += 1

        debug.log(f"New layer created at level {self.level}: {self.stack[self.level]}")
        return premise

    def add_prove(self, premise, add_as_assumption=True):
        if add_as_assumption:
            self.nd.add(Step(premise, StepType.A))

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

    def remove_prove(self, premise):
        if isinstance(premise, Token):
            premise = Premise.from_raw(premise)
        
        if premise in self.stack[self.level].proved:
            debug.log(f"Removing {premise} from the current layer")
            self.stack[self.level].proved.remove(premise)