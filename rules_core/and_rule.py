import debug
from typing import TYPE_CHECKING
from output import Step, StepType
from rules_core.negation import negate
if TYPE_CHECKING:
    from solve import Solver, Premise
    from tokens import TokenState, Token

def and_rule(solver: 'Solver', target: 'Premise', state: 'TokenState', token: 'Token'):
    hand = token.includes(target)

    if hand != 0:
        return introduce_and(solver, state, token)
    else:
        eliminate_and(solver, state, token)
        debug.log("Check if target is proveable with the 'and' rule eliminated")
        return solver.prove(target)


def eliminate_and(solver: 'Solver', state: 'TokenState', token: 'Token'):
    debug.log(f"Applying 'and' elimitation rule on {token}")
    solver.add_prove(token.lh, False)
    solver.nd.add(Step(token.lh, StepType.EA))
    solver.add_prove(token.rh, False)
    solver.nd.add(Step(token.rh, StepType.EA))
    return True

def introduce_and(solver: 'Solver', state: 'TokenState', token: 'Token'):
    debug.log(f"Trying 'and' introduction rule on {token}")
    lh = solver.prove(token.lh)
    rh = solver.prove(token.rh)
    if lh and rh:
        debug.log(f"Introduction of {token} is valid")
        solver.nd.add(Step(token, StepType.IA))
        return True
    debug.log(f"Introduction of {token} is not valid")
    return False