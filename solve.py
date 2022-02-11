import debug
from parse import Parser
from ruler import Ruler
import re
import util
import input
from rules_core.negation import negate

from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from tokens import Token, TokenState


CONCLUDE = ":-"

def init():
    for statement in input.statements:
        debug.log(f"Current statement: '{statement}'")
        solver = Solver(statement)
        result = solver.start()
        if result:
            debug.log(f"Found solution! ({result})\n", debug.SUCCESS)
        else:
            debug.log(f"Solution not found! ({result})\n", debug.ERROR)

class Layer:
    def __init__(self, rest: list['Premise'], target: 'Premise', assumption: 'Premise' = None):
        self.assumption = assumption
        self.assumptions = rest
        if assumption:
            self.assumptions.append(assumption)
        self.target = target

    def __repr__(self):
        return f"Assumptions = {self.assumptions}, target = {self.target}"

class Premise:
    def __init__(self, premise, raw=None):
        self._premise = util.cleanup(premise)
        parser = Parser(self._premise, raw)
        self.raw = parser.raw
        self.literals = parser.literals
        self.tokens = parser.tokens

    def get(self):
        return self._premise

    def negate(self):
        self._premise = f"!({self._premise})"

    def from_raw(raw: list):
        """Returns premise created from raw state"""
        string = str(raw).replace("[", "(").replace("]", ")").replace("'", "").replace(",", "")
        return Premise(string)

    def recreate(self, raw=None):
        premise = str(raw).replace("[", "(").replace("]", ")").replace("'", "").replace(",", "")
        self = Premise(premise, raw)
        return self

    def __repr__(self):
        return f"{self._premise}"

    def __eq__(self, other: any):
        if isinstance(other, str):
            debug.log("Comparing Premise with string!", debug.WARNING)
            return self._premise == other
        elif isinstance(other, Premise):
            return str(self.raw) == str(other.raw)

    def __ne__(self, other: any):
        if isinstance(other, str):
            return self._premise != other
        elif isinstance(other, Premise):
            return self._premise != other._premise
        # if isinstance(other, str):
        #     # Count the number of ! and if they aren't equal self and other aren't equal
        #     c1 = re.findall("!", self._premise)
        #     c2 = re.findall("!", other)
        #     return c1 != c2
        # elif isinstance(other, Premise):
        #     # Count the number of ! and if they aren't equal self and other aren't equal
        #     c1 = re.findall("!", self._premise)
        #     c2 = re.findall("!", other._premise)
        #     return c1 != c2

class Solver:
    def __init__(self, statement: str):
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
        self.stack.append(Layer(self.premises, self.conclusion))

    def start(self):
        debug.log("Starting solver")
        return self.prove(self.conclusion)
        
    def assume(self, at: 'Token', tt: 'Token'):
        premise = Premise.from_raw(at)
        target = Premise.from_raw(tt)

        # Check if assumption is already assumed / proved
        all_assumptions = self._get_stack_assumptions()
        for assumption in all_assumptions:
            if premise == assumption:
                debug.log(f"{premise} is already assumed while trying to prove {target}")
                return True

        debug.log(f"Assuming {premise}, trying to prove {target}")


        
        self.stack.append(Layer(all_assumptions, target, assumption=premise))
        self.level += 1

        debug.log(f"New layer created at level {self.level}: {self.stack[self.level]}")
        return self.prove(target)

    def add_assumption(self, assumption: Premise):
        self.stack[self.level].assumptions.append(assumption)

        # Check if the assumption is the layer target
        if self.stack[self.level].target == assumption:
            debug.log(f"Target '{assumption}' found!", debug.SUCCESS)
            return self.resolve()
        
        return False

    def remove_assumption(self, assumption: Premise):
        self.stack[self.level].assumptions = list(
            filter(
                lambda x: x != assumption,
                self.stack[self.level].assumptions
            )
        )
        # Check if the assumption is the layer target
        if self.stack[self.level].target == negate(assumption):
            debug.log(f"Target contradicts with '{assumption}'")
            return self.reject(assumption)
        
        return False
        
    def prove(self, target: Premise):
        token = target.tokens.get_main_operator()
        debug.log(f"Trying to prove {target}")
        if token:
            return self.ruler.apply(token.operator)(self, target.tokens, token)
        else:
            debug.log(f"No main operator found so target must be a literal")
            # Finding premises with the literal included from the current assumptions (top from stack)
            valids: list[Premise] = []
            for premise in self.stack[-1].assumptions:
                t = target.get().replace("!","")
                for literal in premise.literals:
                    if re.match(r"!?"+t, literal):
                        valids.append(premise)
                        break
            
            i = 0
            while i < len(valids):
                if len(valids[i].literals) != 1:
                    i += 1
                    continue
                # The literal is either p or !p (taking p as en example literal)
                literal = valids[i].literals[0]
                if target == premise:
                    debug.log(f"{target} is valid", debug.SUCCESS)
                    return True
                else:
                    # Make choice point:
                    # Reject immediately and continue
                    # Or declare this layer invalid and everything proved next is false
                    debug.log(f"{target} is invalid")
                    # Hack
                    literal = Premise(literal, raw=[literal])
                    # Reject immediately
                    return self.remove_assumption(literal)

            debug.log(f"Valid premises containing literal {target} = {valids}")
            
            # Make choice point
            for premise in valids:
                # Hack
                found = self.prove(premise)
                if found:
                    return True

            return False

    def resolve(self):
        self.stack.pop()
        if self.level == 0:
            return True

        # Cut of choice point tree, since it was invalid
        self.level -= 1
        debug.log(f"Layer popped. New layer at level {self.level}: {self.stack[self.level]}")
        # ????
        # return False

    def reject(self, rejected: any):
        previous = self.stack.pop()
        if self.level == 0:
            return True

        # Cut of choice point tree, since it was invalid
        self.level -= 1

        self.stack[self.level].assumptions.append(negate(previous.assumption))
        debug.log(f"Layer popped. New layer at level {self.level}: {self.stack[self.level]}")


        # ????
        return self.prove(self.stack[self.level].target)

    def _get_stack_assumptions(self):
        all_assumptions: list[Premise] = []
        for layer in self.stack:
            for assumption in layer.assumptions:
                all_assumptions.append(assumption)
        return all_assumptions