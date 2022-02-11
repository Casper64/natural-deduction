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
    debug.log(f"Trying implication elimitation rule on {token}")

    # Check if token.lh is valid, then token.rh must be valid to
    valid = False
    proved_list = solver.stack[solver.level].proved
    for proved in proved_list:
        if proved == token.lh:
            valid = True
            break
    if valid:
        debug.log(f"{token.lh} is true so {token.rh} is also true following {token}", debug.SUCCESS)
        solver.add_prove(token.rh)
        return True
    debug.log(f"Elimination rule of implication on {token} not valid")
    return False


# Implication introduction rule
def introduce_implication(solver: 'Solver', state: 'TokenState', token: 'Token'):
    debug.log(f"Trying implication introduction rule on {token}")
    # Assume lefthand side and if righthand side follows the 
    premise = solver.assume(token.lh)
    valid = solver.prove(premise)
    if valid:
        debug.log(f"Introducing {token}")
        solver.add_prove(token)
        return True
    debug.log(f"Introduction of {token} not valid")
    return False
