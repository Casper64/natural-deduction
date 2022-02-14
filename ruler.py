import debug

from rules_core.implication import implication, eliminate_implication, introduce_implication
from rules_core.and_rule import and_rule, eliminate_and, introduce_and
from rules_core.negation import negation


from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from tokens import Token, TokenState
    from solve import Solver, Premise

"""
    A rule function takes the premise (str) as argument
    and returns False if the rule is not applicable
    or returns a string tuple with the assumption and the premise to prove
"""
rules = {
    "->": implication,
    "^": and_rule,
    "!": negation
}

introductions = {
    "->": introduce_implication,
    "^": introduce_and
}

eliminations = {
    "->": eliminate_implication,
    "^": eliminate_and
}

operators = ["\^", "=", "V", "->", "!"]


class Ruler:
    def __init__(self):
        self.max = len(rules)
        self.operators = operators

    def apply(self, rule: str) -> Callable[['Solver', 'Premise','TokenState', 'Token'], bool]:
        """Find a rule and return its handler"""
        if rule in rules:
            return rules[rule]
        debug.log(f"Rule '{rule}' not found!", debug.ERROR)
        raise Exception("Rule not found")

    def introduce(self, rule: str) -> Callable[['Solver', 'Premise', 'TokenState'], bool]:
        """Find an introduction rule"""
        if rule in introductions:
            return introductions[rule]
        debug.log(f"Introduction rule '{rule}' not found!", debug.ERROR)
        raise Exception("Rule not found")

    def eliminate(self, rule: str) -> Callable[['Solver', 'Premise', 'TokenState'], bool]:
        """Find an elimination rule"""
        if rule in eliminations:
            return eliminations[rule]
        debug.log(f"Elimination rule '{rule}' not found!", debug.ERROR)
        raise Exception("Rule not found")

    # for ... in ... magic methods
    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if (self.n < self.max):
            # Get the next key while iterating over the rules dict
            key = list(self.rules.keys())[self.n]
            self.n += 1
            return self.rules[key]
        else:
            self.n = 0
            raise StopIteration