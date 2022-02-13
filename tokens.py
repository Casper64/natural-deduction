import debug
import re

class Token:
    def __init__(self, lh: any, operator: str, rh: any, depth=0):
        self.lh = lh
        self.operator = operator
        self.rh = rh
        self.depth = { "default": depth, "local": depth }

    def contains(self, other: 'Token'):
        """Check if a token is a righthand or lefthand value of the current token"""
        b = [other.lh, other.operator, other.rh]
        v = 0
        if self.lh == b:
            v -= 1
        if self.rh == b:
            v += 1
        
        return v

    def includes(self, other: any):
        """Check if some value is contained in the righthand or lefthand value of the current token"""
        v = 0
        if isinstance(other, str):
            if str(self.lh).find(other) != -1:
                v -= 1
            if str(self.rh).find(other) != -1:
                v += 1
        else:
            # Token or Premise
            if str(self.lh).find(str(other)) != -1:
                v -= 1
            if str(self.rh).find(str(other)) != -1:
                v += 1

        return v

    def raw(self):
        return [self.lh, self.operator, self.rh]

    def __repr__(self, key="default"):
        # return f"[depth={self.depth[key]}] {self.lh} {self.operator} {self.rh}"
        s = f"{self.lh} {self.operator} {self.rh}"
        if self.depth["default"] != 0:
            s = f"({s})"
        return s
        

class TokenState:
    # Had to initialize state as None, because instantiating it as an empty dict would leave a mutatable value
    # As argument, which would only be instantiated once
    # See https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
    def __init__(self, premise: str, state: dict[int, Token] = None):
        if state is None:
            state = {}
        self.state = state
        self.n = 0
        self._premise = premise

    def append(self, token: Token):
        """Insert a token to the state"""
        # FIX for a ^ b ^c:
        # Raw will be ['a','^','b','^','c']
        # Check if lefthand is already included on the previous righthand
        # If so set lefthand to one level up with raw token = ['b','^','c']

        self.n += 1

        for id, t in self.state.items():
            if t.depth["default"] > token.depth["default"]:
                continue
            # Implement the fix
            if t.depth["default"] == token.depth["default"]:
                if t.rh == token.lh:
                    self.state[id].rh = self.n
                    token.depth["local"] =  t.depth["local"] + 1

                continue
            hand = t.contains(token)
            if hand == 0:
                continue
            elif hand == -1:
                self.state[id].lh = self.n
            elif hand == 1:
                self.state[id].rh = self.n
        self.state[self.n] = token

    def get_main_operator(self):
        """Find the main operator from this state"""
        if len(self.state.values()) == 0:
            return None
        # Find item where the local depth = 0, should be one item only!
        zeros: list[Token] = list(filter(lambda x : x.depth["local"] == 0 ,list(self.state.values())))
        if len(zeros) > 1:
            debug.log(f"Invalid number of main operators found in '{self._premise}", debug.WARNING)
        elif len(zeros) == 0:
            debug.log(f"No main operators found in '{self._premise}", debug.ERROR)
        main = zeros[0]
        return self.find_with_state(main)

    def find_with_state(self, token: Token):

        # Simple case when a side is just one integer
        if isinstance(token.rh, int):
            return self.find_with_state(Token(token.lh, token.operator, self.state[token.rh]))
        elif isinstance(token.lh, int):
            return self.find_with_state(Token(self.state[token.lh], token.operator, token.rh))

        # Case where there are multiple replacebles in one hand
        if isinstance(token.rh, Token):
            token.rh = self.find_with_state(token.rh)
        if isinstance(token.lh, Token):
            token.lh = self.find_with_state(token.lh)

        return token

    def __repr__(self):
        return str(self.state)
        

