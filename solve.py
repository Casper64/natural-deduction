import debug
from ruler import Ruler
import input
from output import NaturalDeductionTree, Step, StepType
from premise import Premise
from fsm import MasterPool, ProveFSM, Pool

CONCLUDE = ":-"

def init():
    for statement in input.statements:
        debug.log(f"Current statement: '{statement}'")
        solver = Solver(statement)
        if solver.start():
            debug.log(f"Found solution!\n", debug.SUCCESS)
        else:
            debug.log(f"Solution not found!\n", debug.ERROR)
        solver.nd.close()



class Solver:
    def __init__(self, statement: str):
        self.solved = False
        self.nd = NaturalDeductionTree(statement)

        self.statement = statement
        a = statement.split(CONCLUDE)
        if len(a) < 2:
            raise Exception("Statement does include a conclusion")
        elif len(a) > 2:
            raise Exception("Statement includes multiple conclusions")
        
        debug.log(f"Parsing '{statement}'")

        self.premises = [Premise(x) for x in a[0].split(",")]
        self.conclusion = Premise(a[1])
        
        for premise in self.premises:
            self.nd.add(Step(premise, StepType.P))

        debug.log(f"Raw representation of conclusion {self.conclusion.raw}")
        debug.log(f"With tokens = {self.conclusion.tokens}")

        if not self.conclusion.get():
            debug.log("No conclusion is found", debug.ERROR)
            raise Exception("A conclusion must be provided")
        else:
            debug.log("Found valid premise(s) and conclusion", debug.SUCCESS)

        self.ruler = Ruler()

    def start(self):
        debug.log("Starting solver")
        
        pool = MasterPool.add()
        fsm = ProveFSM(self.premises, self.conclusion, pool.id)
        pool.add_state(fsm)

        i = 0
        found = (None, None)
        while (found := pool.is_valid()) and found[0] == None and i < 7:
            debug.log(f"New step, nr. of states = {len(pool.states)}", debug.bcolors.OKBLUE)
            pool.update()
            debug.log("============")
            i += 1
        print(found)
        self.nd.steps.extend(found[1].steps)
        return found[0]
        # i = 0
        # while not fsm.is_valid():
        #     fsm.send(i)
        #     i += 1
        # for i in range(10):
        #     fsm.send(i)
        #     if fsm.is_valid():
        #         debug.log("valid!", debug.SUCCESS)
        #         self.solved = True
        #         return

        # self.solved = False

        