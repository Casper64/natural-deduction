import debug
from rules_core.implication import implication, test_implication, introduce_implication
from rules_core.negation import negation, test_negation
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
    "!": negation
}
eliminate = rules

tests = {
    "->": test_implication,
    "!": test_negation
}

operators = ["\^", "=", "V", "->", "!"]

introduce = {
    "->": introduce_implication
}


class Ruler:
    def __init__(self):
        self.rules = rules
        self.tests = tests
        self.max = len(rules)
        self.operators = operators

    # ======= ???:begin =======

    def apply(self, rule: str) -> Callable[['Solver', 'TokenState', 'Token'], bool]:
        """Find a rule and return its handler"""
        if rule in self.rules:
            return self.rules[rule]
        debug.log(f"Rule '{rule}' not found!", debug.ERROR)
        raise Exception("Rule not found")

    def test(self, premise: str):
        """Returns which rule matches the premise"""
        for name, test in tests.items():
            if test(premise):
                return name
        return None

    # ======= ???:end =======

    def introduce(self, operator: str) -> Callable[['Solver', 'TokenState', 'Token'], bool]:
        """Find a rule and return its handler"""
        if operator in introduce:
            return introduce[operator]
        debug.log(f"Operator '{operator}' not found!", debug.ERROR)
        raise Exception("Operator not found")

    def eliminate(self, operator: str) -> Callable[['Solver', 'TokenState', 'Token'], bool]:
        """Find a rule and return its handler"""
        if operator in eliminate:
            return eliminate[operator]
        debug.log(f"Operator '{operator}' not found!", debug.ERROR)
        raise Exception("Operator not found")

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