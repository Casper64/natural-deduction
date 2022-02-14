import debug
from typing import TYPE_CHECKING
from output import Step, StepType
from rules_core.negation import negate
if TYPE_CHECKING:
    from solve import Solver, Premise
    from tokens import TokenState, Token

def implication(solver: 'Solver', target: 'Premise', state: 'TokenState', token: 'Token'):
    hand = token.includes(target)

    if hand == 1:
        return eliminate_implication(solver, state, token)
    elif hand == -1:
        return introduce_implication(solver, state, token)

    debug.log("Hand is equal!!", debug.WARNING)
    return False

# Implication elimination rule
def eliminate_implication(solver: 'Solver', state: 'TokenState', token: 'Token'):  
    debug.log(f"Trying implication elimitation rule on {token}")

    # Check if token.lh is already proved, then token.rh must be valid to
    valid = False
    proved_list = solver.stack[solver.level].proved
    neg = negate(token.lh)
    for proved in proved_list:
        if proved == token.lh:
            valid = True
            break
        # Breakout!!
        if proved == neg:
            debug.log(f"Elimination rule of implication on {token} not valid, contradicts with {proved}")
            solver.assume(token.lh, token.rh)
            solver.reject(neg)
            solver.remove_prove(token)
            return False

    # Try to prove token.lh if not already proved
    if not valid:
        debug.log("Lefthand of implication wasn't already proved so trying now")
        valid = solver.prove(token.lh)
    
    if valid:
        debug.log(f"{token.lh} is true so {token.rh} is also true following {token}", debug.SUCCESS)
        solver.nd.add(Step(token.rh, StepType.EI))
        solver.add_prove(token.rh, False)
        return True
    debug.log(f"Elimination rule of implication on {token} not valid")
    return introduce_implication(solver, state, token)


# Implication introduction rule
def introduce_implication(solver: 'Solver', state: 'TokenState', token: 'Token'):
    debug.log(f"Trying implication introduction rule on {token}")
    # Assume lefthand side and if righthand side follows the implication is valid
    if not isinstance(token.lh, str):
        premise = token.lh
        if not solver.prove(token.lh):
            debug.log(f"Can't prove {token.lh}, so introduction of {token} is not valid")
            return False
        debug.log(f"Continuing Trying implication introduction rule on {token}")
    else:
        premise = solver.assume(token.lh, token.rh)
    valid = solver.prove(token.rh, StepType.II)
    if valid:
        debug.log(f"Introducing {token}")
        solver.nd.add(Step(token, StepType.II))
        solver.add_prove(token, False)
        return True

    debug.log(f"Introduction of {token} not valid")
    # From now on everything that is proved is false, because the assumption will end in a cotnradiction
    solver.nd.add(Step(token.rh, StepType.EI))
    solver.reject(premise)
    return False
