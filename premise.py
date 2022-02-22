from tokens import Token
import util
from parse import Parser
import debug

class Premise:
    id = 0
    def __init__(self, premise: any, raw=None):
        self._premise = util.cleanup(premise)
        self._parse(raw)
        self.id = Premise.id
        Premise.id += 1

    def create(premise: any):
        if isinstance(premise, Premise):
            return premise
        elif isinstance(premise, list):
            return Premise.from_raw(premise)
        elif isinstance(premise, Token):
            return Premise.from_raw(premise.get_raw())
        else:
            return Premise(premise)

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
        def search(a):
            if isinstance(a, list):
                for i, b in enumerate(a):
                    # Prevent weird slicing of string
                    if not isinstance(b, str):
                        a[i:i+1] = search(b)
            elif isinstance(a, Token):
                a = a.get_raw()
            elif isinstance(a, Premise):
                a = a.raw
            return a
        raw = search(raw)
        string = util.raw_to_str(raw)
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
