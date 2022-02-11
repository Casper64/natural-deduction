import re
from debug import log
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from solve import Solver, Premise
    from tokens import TokenState, Token

def test_negation(string: str):
    match = bool(re.search("!", string))
    return match

def negation(solver: 'Solver', state: 'TokenState', token: 'Token'):    
    
    log(f"Applying negation rule on {token}")

    # premise = string.replace("!")
    

    return True
    
def negate(premise: any):
    if isinstance(premise, list):
        for i in range(len(premise)):
            premise[i] = negate(premise[i])
        return premise
    elif isinstance(premise, str):
        count = len(re.findall("!", premise))
        if count == 0:
            return "!"+premise
        else:
            return premise.replace("!", "")
    else:
        # premise must be of type 'Premise'
        raw = negate(premise.raw)
        return premise.recreate(raw)
