from abc import abstractmethod
import debug
from premise import Premise
from tokens import Token
from copy import deepcopy
from rules_core.negation import negate
from output import Step, StepType
import re

class MasterPool:
    pools: list['Pool'] = []

    def add():
        pool = Pool()
        MasterPool.pools.append(pool)
        return pool

    def get(id: int):
        for x in MasterPool.pools:
            if x.id == id:
                break
        else:
            x = None
        return x

    def remove(pool: 'Pool'):
        MasterPool.pools.remove(pool)


class Pool:
    id = 0
    def __init__(self):
        self.states: list['FSM'] = []
        self.id = Pool.id
        Pool.id += 1

    def add_state(self, fsm: 'FSM'):
        fsm_copy = deepcopy(fsm)
        fsm_copy.id = FSM.id
        FSM.id += 1
        self.states.append(fsm_copy)
        return fsm_copy.id

    def update(self):
        

        # Chose a while loop, because Masterpool.states can change while looping
        # i = 0
        # while i < len(MasterPool.states):
        #     fsm = MasterPool.states[i]
        #     fsm.update()
        #     debug.log("============")
        #     i += 1

        for fsm in self.states:
            fsm.update()
            

    def remove(self, states: list[int]):
        self.states = list(filter(lambda x: x.id not in states, self.states))

    def is_valid(self, states: list[int] = None):
        # Get all the fsm's where id is in the provided list
        if states:
            states = list(filter(lambda x: x.id in states, self.states))
            check_depth = False
        else:
            states = self.states
            check_depth = True

        all_false = True
        for fsm in states:
            if check_depth and fsm.depth != 0:
                continue

            res = fsm.is_valid()
            if res == True:
                return (True, fsm)
            elif res == False and check_depth:
                return (False, fsm)
            else:
                all_false = False


        if all_false:
            return (False, states)
        return (None, None)

    def __repr__(self):
        return str(self.states)

class FSM:
    id = 0

    def __init__(self, pool: int, depth):
        self.pool = pool
        self.current_state = self.init
        self.stopped = False
        self.parameters = []
        self.id = FSM.id
        self.depth = depth
        FSM.id += 1
        self.steps: list[Step] = []

    def update(self):
        try:
            self.current_state()
        except StopIteration:
            self.stopped = True

    def is_valid(self):
        if self.stopped:
            return False
        elif self.current_state == self.end:
            return True

    def splice(self):
        pool = MasterPool.get(self.pool)
        id = pool.add_state(self)

    @abstractmethod
    def init(self):
        pass

    def end(self):
        debug.log(f"{self.id}: End state reached")

    def __repr__(self):
        return f"id={self.id}, state={self.__class__.__name__}.{self.current_state.__name__}"

class ProveFSM(FSM):
    def __init__(self, assumptions: list[Premise], target: Premise, pool: Pool, depth=0):
        FSM.__init__(self, pool, depth)
        
        self.assumptions = assumptions
        self.target = target

        self.negation_state = {
            "waiting": False
        }
        self.assumptions_state = {
            "waiting": False
        }

    def init(self):
        # Start the solver
        debug.log(f"{self.id}: Starting fsm p = {self.target}")
        token = self.target.tokens.get_main_operator()
        if token:
            self.current_state = self.operator
            self.parameters = [token]
        else:
            self.current_state = self.literal

    # ======== Literal Path ========
    def literal(self):
        """State when the target is a literal.
            Checking if literal is a negation. And if the literal is proved"""
        debug.log(f"{self.id}: Target {self.target} is a literal")
        # Check if the literal is negation
        if "!" in self.target.get():
            self.current_state = self.is_negation
            self.splice()
        
        # Check if the literal is proved
        for premise in self.assumptions:
            if premise == self.target:
                self.steps.append(Step(premise, StepType.RI))
                self.current_state = self.literal_is_proved
                return
            elif negate(premise) == self.target:
                debug.log(f"{self.id}: {self.target} contradicts!")
                self.stopped = True
                self.current_state = self.end
                self.steps.append(Step(premise, StepType.RI))
                return
        self.current_state = self.get_literal_assumptions

    # @static_vars(waiting=False, fsm=None)
    def is_negation(self):
        """State when the target is a literal and a negation.
            Applying double negation rule, thus proving !p"""
        state = self.negation_state
        neg = negate(self.target)
  
        if state["waiting"]:
            debug.log(f"{self.id}: Waiting for prove of {neg}")
            debug.log("-"*(self.depth + 5))
            state["pool"].update()
            debug.log("-"*(self.depth + 5))
            found = state["pool"].is_valid()
            if found[0] == True:
                debug.log(f"{self.id}: {self.target} contradicts!")
                self.stopped = True
                self.current_state = self.end
                MasterPool.remove(state["pool"])

                self.steps.extend(found[1].steps)
            elif found[0] == False:
                debug.log(f"{self.id}: {self.target} is True!")
                self.current_state = self.end

        else:
            # Initialize a new Pool for proving !target
            debug.log(f"{self.id}: Literal {self.target} is a negation")
            state["waiting"] = True
            pool = MasterPool.add()
            fsm = ProveFSM(self.assumptions, neg, 0)
            pool.add_state(fsm)
            state["pool"] = pool
    
        
    def literal_is_proved(self):
        """State when the target is a literal and is proved.
            Returning true or continuing the fsm"""
        debug.log(f"{self.id}: Literal {self.target} is already proved")

        self.current_state = self.get_literal_assumptions
        self.splice()

        
        self.current_state = self.end

    def get_literal_assumptions(self):
        """Get assumptions containing the target"""
        
        # Get all the premises where the literal is used
        valids: list[Premise] = []
        for premise in self.assumptions:
            for literal in premise.literals:
                if re.match(r"!?"+self.target.get(), literal):
                    valids.append(premise)
                    break
        
        # If there are no valids the premise can't be proved
        if len(valids) == 0:
            debug.log(f"{self.id}: No valid premises were found trying to prove {self.target}")
            return False

        # If there are no valids the premise can't be proved
        if len(valids) == 0:
            debug.log(f"No valid premises were found trying to prove {self.target}")
            self.current_state = self.end
            self.stopped = True

        debug.log(f"{self.id}: Valid premises containing literal {self.target} = {valids}")

        for premise in valids:
            # Token should be always defined, because the cases where the target contradicts with a
            # literal or is equal to should all be covered
            token = premise.tokens.get_main_operator()
            self.current_state = self.apply_elimination
            self.parameters = [token]
   

    def apply_elimination(self):
        """Apply elimination to the assumptions gotten from 'get_literal_assumptions'"""
        debug.log(f"{self.id}: Applying elimination rule on {self.parameters[0]} with target = {self.target}")
        state = self.assumptions_state


    # ======== operator Path ========
    def operator(self):
        """State when the target contains an operator"""
        pass