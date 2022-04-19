
from multipleVMSolver import OffloadingSolver
import rankerConfig
import time
import numpy as np

# toleranceWindow = 0
# mode = "latency"  
# availResources =  {'cores':1000, 'mem_mb':500000}

class CIScheduler:

    def __init__(self,  workflow, mode,toleranceWindow) :
        self.decisionModes = rankerConfig.decisionMode
        self.workflow = workflow
        self.mode = mode
        self.toleranceWindow = toleranceWindow

    def suggestBestOffloadingSingleVM(self,  availResources, alpha):
        decisions = []
        for decisionMode in self.decisionModes:
            solver = OffloadingSolver(None,None, self.workflow, self.mode,decisionMode, self.toleranceWindow)
            x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
            decisions.append(x)
            print("ModeGHazal: {}, Decision: {}".format(decisionMode, x))


    
        finalDecision = [[0]*len(decisions[0][0])]*len(decisions[0])
        # for func in range(len(decisions[0])):
        #     for vm in range(len(decisions[0][0])):
        #         finalDecision[func][vm] = sum([(decision[func][vm]) for decision in decisions ])/len(decisions)
        #         if finalDecision[func][vm] == 1:
        #             finalDecision[func][vm] = 0.9
        #         print("jkesfhkjbas", finalDecision)
        # finalDecision = sum([(decision) for decision in decisions ])/len(decisions)
        for decision in decisions:
            finalDecision = np.add(finalDecision,decision)
        finalDecision = finalDecision / len(decisions)
        finalDecision = np.where(finalDecision == 1, 0.9, finalDecision)
        return list(finalDecision)


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    start_time = time.time()
    workflow = "TestWorkflow"
    # workflow = "Text2SpeechCensoringWorkflow"
    mode = "latency"
    toleranceWindow = 0
    solver = CIScheduler(workflow, mode,toleranceWindow)
    availResources =  {'cores':1000, 'mem_mb':500000}
    verbose = True
    alpha = 1
    x = solver.suggestBestOffloadingSingleVM(availResources, alpha)
    print("Final Decision: {}". format(x))
    print("--- %s seconds ---" % (time.time() - start_time))