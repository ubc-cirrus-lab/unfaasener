from mip import *

class Solver:

    def SuggestBestOffloadingSingleVM(optimizationMode, offloadingCandidates, availResources, alpha, verbose):
        """
        Returns a list of 0's (no offloading) and 1's (offloading)
        - optimizationMode: "cost"   or   "latency"
        - offloadingCandidates: list of function objects
        - availResources: {'cores':C, 'mem_mb':M}
        - alpha: FP number in [0, 1]
        """
        if optimizationMode == "cost":
            model = Model(sense=MINIMIZE, solver_name=CBC)
            x = [model.add_var(var_type=BINARY) for s in offloadingCandidates]

            # optimization goal
            model.objective = xsum( [alpha*(1 - x[i])*offloadingCandidates[i].GetServerlessCostEstimate() + \
                                (1 - alpha)*(abs(x[i] - offloadingCandidates[i].IsOffloaded() )) \
                                    for i in range(len(x))] )

            # Memory constraint
            model.add_constr( xsum( [x[i]*offloadingCandidates[i].GetMem() \
                                for i in range(len(x))] ) <= availResources['mem_mb'],
                                priority=1)
            # CPU constraint
            model.add_constr( xsum( [x[i]*offloadingCandidates[i].GetCPU() \
                                for i in range(len(x))] ) <= availResources['cores'],
                                priority=1)

            # solve
            status = model.optimize(max_seconds=30)
            if verbose:
                print(status)

            # check if no solution was found, each the condition
            if [x[i].x for i in range(len(x))] == [None for i in range(len(x))]:
                print("No solution could be found!")

        elif optimizationMode == "latency":
            model = Model(sense=MINIMIZE, solver_name=CBC)
            x = [model.add_var(var_type=BINARY) for s in offloadingCandidates]
            # TODO
            pass
        else:
            print("Invalid optimization mode!")
            return [0 for i in range(len(offloadingCandidates))]

        offloadingDecisions = [x[i].x for i in range(len(x))]
        return offloadingDecisions