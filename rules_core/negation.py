import re
from debug import log
from tokens import Token
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from solve import Solver, Premise
    from tokens import TokenState, Token

def test_negation(string: str):
    match = bool(re.search("!", string))
    return match

def negation(solver: 'Solver', target: 'Premise', state: 'TokenState', token: 'Token'): 
    
    log(f"Applying negation rule on {token}")

    return True


    
def negate(premise: any):
    if isinstance(premise, list):
        p = []
        for i in range(len(premise)):
            p.append(negate(premise[i]))
        return premise
    elif isinstance(premise, str):
        count = len(re.findall("!", premise))
        if count == 0:
            return "!"+premise
        else:
            return premise.replace("!", "")
    elif isinstance(premise, Token):
        lh = negate(premise.lh)
        rh = negate(premise.rh)
        return Token(lh, premise.operator, rh, premise.depth)
    else:
        # premise must be of type 'Premise'
        string = str(premise)
        if string[0] == "!":
            string = string[1:]
        else:
            # ??? or string = "!("+string+")"
            string = "!"+string
        return premise.duplicate(string)
