import re
import debug
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from solve import Solver
    from tokens import TokenState, Token

def test_implication(string: str):
    match = bool(re.search("->", string))
    return match

# Implication elimination rule
def implication(solver: 'Solver', state: 'TokenState', token: 'Token'):    
    debug.log(f"Applying implication rule on {token}")

    # Check if token.lh is valid, then token.rh must be valid to

    valid = solver.assume(token.lh, token.rh)
    if valid:
        debug.log(f"Applying Elimination rule of implication on {token}")
        found = solver.add_assumption(token.rh)
        if found:
            return found
    debug.log(f"Elimination rule of implication on {token} not valid")
    return False
