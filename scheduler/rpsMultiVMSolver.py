import os
import json
import configparser
from pathlib import Path
from LatencyModel import LatencyModel
from gekko import GEKKO
from Estimator import Estimator
import itertools

# Non-linear optimzation models for cost and latency


class rpsOffloadingSolver:
    def __init__(self, workflow, mode, decisionMode, toleranceWindow, rps, testingFlag):
        self.testingFlag = testingFlag
        self.rps = rps
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.muFactor = self.rankerConfig["muFactor"]
        if mode == "latency":
            with open(
                (
                    (os.path.dirname(os.path.abspath(__file__)))
                    + "/data/"
                    + str(workflow)
                    + "/"
                    + "slackData.json"
                ),
                "r",
                os.O_NONBLOCK,
            ) as outfile:
                self.slacksDF = json.load(outfile)
            with open(
                (
                    (os.path.dirname(os.path.abspath(__file__)))
                    + "/data/"
                    + str(workflow)
                    + "/"
                    + "slackDurations.json"
                ),
                "r",
                os.O_NONBLOCK,
            ) as outfile:
                self.slackDurationsDF = json.load(outfile)
        with open(
            (
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(workflow)
                + "/"
                + "pubSubSize.json"
            ),
            "r",
            os.O_NONBLOCK,
        ) as outfile:
            self.pubSubSize = json.load(outfile)
        with open(
            (
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(workflow)
                + "/"
                + "Costs.json"
            ),
            "r",
            os.O_NONBLOCK,
        ) as outfile:
            self.serverlessCosts = json.load(outfile)
        self.estimator = Estimator(workflow)
        self.terminals = []
        self.allPathsSlack = {}
        self.allPaths = []
        self.decisionMode = decisionMode
        if self.decisionMode == None:
            self.decisionMode = "default"
        self.toleranceWindow = toleranceWindow
        self.GCP_MB2GHz = {
            125: 0.2,
            250: 0.4,
            500: 0.8,
            1000: 1.4,
            2000: 2.4,
            4000: 4.8,
            8000: 4.8,
        }
        self.jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + ".json"
        )

        with open(self.jsonPath, "r") as json_file:
            self.workflow_json = json.load(json_file)
        self.optimizationMode = mode
        self.offloadingCandidates = self.workflow_json["workflowFunctions"]
        self.lastDecision = self.workflow_json["lastDecision" + "_" + self.decisionMode]
        self.successors = self.workflow_json["successors"]
        self.predecessors = self.workflow_json["predecessors"]
        self.initial = self.workflow_json["initFunc"]
        self.memories = self.workflow_json["memory"]

    def getAllPaths(self):
        """
        Returns all possible paths in the dag starting from the initial node to a terminal node
        """
        terminals = []
        for node in self.offloadingCandidates:
            if len(self.successors[self.offloadingCandidates.index(node)]) == 0:
                terminals.append(node)
        queue = [[self.initial]]
        visited = set()
        results = []
        while queue:
            path = queue.pop(0)
            lastNode = path[-1]
            if lastNode in terminals:
                results.append(path)
                continue
            elif tuple(path) not in visited:
                for successor in self.successors[
                    self.offloadingCandidates.index(lastNode)
                ]:
                    new_path = path.copy()
                    new_path.append(successor)
                    queue.append(new_path)
                visited.add(tuple(path))
        for path in results:
            self.allPaths.append(path)

    def getDuration(self, func):
        """
        Returns estimated duration for each function based on the dataframe
        """
        duration = self.slackDurationsDF[func][self.decisionMode]
        return duration

    def getCriticalPathDuration(self):
        """
        Returns estimated duration for the critical path
        """
        cpDuration = max(self.allPathsSlack.keys())
        return cpDuration

    def getSlackForPath(self):
        """
        Returns a list consisting of all paths in the workflow and their duration as a dictionary
        """
        for path in self.allPaths:
            nodes = []
            comNodes = []
            duration = 0
            for s in range(len(path) - 1):
                comNodes.append(path[s] + "-" + path[s + 1])
            nodes = path + comNodes

            for node in nodes:
                duration += self.getDuration(node)
            self.allPathsSlack[duration] = path

    def getVMexecution(self, offloadingCandidate, vm):
        vm = self.estimator.getFuncExecutionTime(
            offloadingCandidate, ("vm" + str(vm)), self.decisionMode
        )
        if vm == 0:
            vm = self.estimator.getFuncExecutionTime(
                offloadingCandidate, "s", self.decisionMode
            )

        return vm

    def addedExecLatency(self, offloadingCandidate, vm):
        """
        Returns estimated added execution time which is caused by offloading a serverless function to VM
        """
        # print("ExecTime:::", offloadingCandidate, "-on--->", vm)
        serverless = self.estimator.getFuncExecutionTime(
            offloadingCandidate, "s", self.decisionMode
        )
        vm = self.estimator.getFuncExecutionTime(
            offloadingCandidate, ("vm" + str(vm)), self.decisionMode
        )
        if vm == 0:
            vm = self.estimator.getFuncExecutionTime(
                offloadingCandidate, "s", self.decisionMode
            )
        diff = vm - serverless
        # if diff != 0:
        #     print("EXECUTION DIFF:::",offloadingCandidate, "::::", diff)
        return diff

    # Function for added end-to-end latency by offloading a function to VM
    def addedComLatency(self, parent, child):
        """
        Returns estimated added end-to-end latency by offloading a function to VM
        """
        latencyModel = LatencyModel()
        msgSize = self.pubSubSize[child]
        latency = latencyModel.getLinearAddedLatency(msgSize)
        return latency

    def getMem(self, offloadingCandidate):
        """
        Returns required memory for the function based on the dataframe
        """
        mem = self.memories[self.offloadingCandidates.index(offloadingCandidate)]
        mem = mem * 1000
        return mem

    def getCPU(self, mem):
        """
        Returns required CPU for the function based on the dataframe
        """
        cpu = self.GCP_MB2GHz[mem]
        return float(cpu)

    def GetServerlessCostEstimate(self, offloadingCandidate):
        """
        Returns estimated cost for the function based on the dataframe
        """
        cost = self.serverlessCosts[offloadingCandidate][self.decisionMode]
        return cost

    def IsOffloaded(self, offloadingCandidate, vm):
        """
        Returns previous offloadind decision for the function
        """
        decision = self.lastDecision[
            self.offloadingCandidates.index(offloadingCandidate)
        ][vm]
        if decision == 0:
            return 0
        else:
            return 1

    def onCriticalPath(self, offloadingCandidate):
        """
        Returns a boolean value(0:The function is on the critical path, 1: The function is not on the critical path)
        - offloadingCandidate: function we needed to check
        """
        if (self.slacksDF[offloadingCandidate][self.decisionMode]) == 0:
            return 1
        else:
            return 0
        # cp = self.paths[0][ self.offloadingCandidates.index(offloadingCandidate) ]
        # return cp

    def sameVM(self, node, parent):
        if node == parent:
            return 0
        else:
            return 1

    def getChildIndexes(self, offloadingCandidate):
        """
        Returns indexes for the children of a function based on sucessors
        """
        childrenIndexes = []
        children = self.successors[self.offloadingCandidates.index(offloadingCandidate)]
        for child in children:
            childrenIndexes.append(self.offloadingCandidates.index(child))
        return childrenIndexes

    def getParentIndexes(self, offloadingCandidate):
        """
        Returns indexes for the parents of a function based on sucessors
        """
        parentIndexes = []
        parents = self.predecessors[
            self.offloadingCandidates.index(offloadingCandidate)
        ]
        for parent in parents:
            parentIndexes.append(self.offloadingCandidates.index(parent))
        return parentIndexes

    def GetDatastoreCost(self, mode):
        cost = self.estimator.getUnitCost_Datastore(mode)
        return cost

    def getCommunicationLatency(self, child, parent, childHost, parentHost, mode):
        addedLat = self.estimator.getComLatency(
            child, parent, childHost, parentHost, mode
        )
        if addedLat == "NotFound":
            added = self.addedComLatency(parent, child)
            return added
        else:
            return addedLat

    def GetPubsubCost(self, offloadingCandidate, child):
        """
        Returns estimated pub/sub cost based on the dataframe
        """
        cost = self.estimator.getComCost(self.pubSubSize[child])
        return cost

    def suggestBestOffloadingMultiVM(self, availResources, alpha, verbose):
        """
        Returns a list of 0's (no offloading) and 1's (offloading)
        - optimizationMode: "cost"   or   "latency"
        - offloadingCandidates: list of function objects
        - availResources: [{'cores':C, 'mem_mb':M} ... {'cores':C, 'mem_mb':M}]
        - alpha: FP number in [0, 1]
        """
        offloadingCandidates = self.offloadingCandidates
        if self.optimizationMode == "cost":
            model = GEKKO(remote=False)
            zero = model.Const(0)
            one = model.Const(1)
            alphaConst = model.Const(alpha)

            tempGoalVar = [
                [
                    model.Var(lb=0, ub=1, integer=True)
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            offloadingDecisions = [
                [
                    model.Var(
                        lb=0,
                        ub=100,
                        integer=True,
                        name=("function:" + str(j) + " resource:" + str(i)),
                    )
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            # Constraint on only having a single or zero one for each vm decision for a function
            for function in offloadingDecisions:
                model.Equation(sum([function[i] for i in range(len(function))]) <= 100)

            # Constraint on checking available memory of each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            (
                                self.rps
                                * self.estimator.get_num_per_req(
                                    offloadingCandidates[function + 1], self.testingFlag
                                )
                                * (
                                    self.getVMexecution(
                                        offloadingCandidates[function + 1], VMIndex
                                    )
                                    * 0.001
                                )
                                * (offloadingDecisions[function + 1][VMIndex] / 100)
                                * (self.getMem(offloadingCandidates[function + 1]))
                            )
                            for function in range(len(offloadingDecisions) - 1)
                        ]
                    )
                    <= availResources[VMIndex]["mem_mb"]
                )
            # Constraint on checking available number of  cores for each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            (
                                self.rps
                                * self.estimator.get_num_per_req(
                                    offloadingCandidates[function + 1], False
                                )
                                * (
                                    self.getVMexecution(
                                        offloadingCandidates[function + 1], VMIndex
                                    )
                                    * 0.001
                                )
                                * (offloadingDecisions[function + 1][VMIndex] / 100)
                                * self.muFactor
                                # * (
                                #     self.getCPU(
                                #         self.getMem(offloadingCandidates[function + 1])
                                #     )
                                # )
                                # * 2
                            )
                            for function in range(len(offloadingDecisions) - 1)
                        ]
                    )
                    <= availResources[VMIndex]["cores"]
                )

            # Constraint for showing the first Function should run as serverless
            for i in range(len(offloadingDecisions[0])):
                model.Equation(offloadingDecisions[0][i] == 0)

            for vm in range(len(availResources)):
                for i in range(len(offloadingDecisions)):
                    model.Equation(
                        tempGoalVar[i][vm] == model.min2(offloadingDecisions[i][vm], 1)
                    )
            model.Minimize(
                model.sum(
                    [
                        (
                            ((10**5) * 2)
                            * (1 - alphaConst)
                            * self.rps
                            * self.estimator.get_num_per_req(
                                offloadingCandidates[i], False
                            )
                            * self.GetServerlessCostEstimate(offloadingCandidates[i])
                            * (
                                (
                                    100
                                    - (
                                        model.sum(
                                            [
                                                (offloadingDecisions[i][vm])
                                                for vm in range(len(availResources))
                                            ]
                                        )
                                    )
                                )
                                / 100
                            )
                        )
                        + (
                            (1 - alphaConst)
                            * self.rps
                            * self.estimator.get_num_per_req(
                                offloadingCandidates[i], False
                            )
                            * (
                                self.GetDatastoreCost("w")
                                + self.GetDatastoreCost("d")
                                + self.GetDatastoreCost("r")
                            )
                            * (
                                (
                                    (
                                        model.sum(
                                            [
                                                (offloadingDecisions[i][vm])
                                                for vm in range(len(availResources))
                                            ]
                                        )
                                    )
                                )
                                / 100
                            )
                        )
                        + model.sum(
                            [
                                (
                                    # (
                                    #     ((10**5) * 2)
                                    #     * (1 - alphaConst)
                                    #     * (
                                    #         model.sum(
                                    #             [
                                    #                 (
                                    #                     1
                                    #                     - (
                                    #                         (
                                    #                             offloadingDecisions[i][
                                    #                                 vm
                                    #                             ]
                                    #                             / 100
                                    #                         )
                                    #                         * (
                                    #                             offloadingDecisions[j][
                                    #                                 vm
                                    #                             ]
                                    #                             / 100
                                    #                         )
                                    #                     )
                                    #                 )
                                    #                 * self.rps
                                    #                 *
                                    #                 self.estimator.get_num_per_req(offloadingCandidates[i], False)
                                    #                 *
                                    #                 self.estimator.get_num_per_req(offloadingCandidates[j], False)
                                    #                 * self.GetPubsubCost(
                                    #                     (offloadingCandidates[i]),
                                    #                     (offloadingCandidates[j]),
                                    #                 )
                                    #                 for j in self.getChildIndexes(
                                    #                     offloadingCandidates[i]
                                    #                 )
                                    #             ]
                                    #         )
                                    #     )
                                    # )
                                    # +
                                    (
                                        (10**3)
                                        * (alphaConst)
                                        * (
                                            model.abs2(
                                                tempGoalVar[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                                for vm in range(len(availResources))
                            ]
                        )
                        for i in range(len(offloadingDecisions))
                    ]
                )
            )

            # solve
            model.options.SOLVER = 1

            try:
                model.solve(disp=False)
                offloadingDecisionsFinal = [
                    [
                        (offloadingDecisions[j][i].value)[0]
                        for i in range(len(availResources))
                    ]
                    for j in range(len(offloadingCandidates))
                ]

                usedResources = sum(
                    [
                        (
                            self.rps
                            * self.estimator.get_num_per_req(
                                offloadingCandidates[function + 1], False
                            )
                            * (
                                self.getVMexecution(
                                    offloadingCandidates[function + 1], 0
                                )
                                * 0.001
                            )
                            * (offloadingDecisionsFinal[function + 1][0] / 100)
                            * (
                                self.getCPU(
                                    self.getMem(offloadingCandidates[function + 1])
                                )
                            )
                        )
                        for function in range(len(offloadingDecisions) - 1)
                    ]
                )
                # for function in range(len(offloadingDecisions) - 1):
                # print("-------")
                # print("funct::", offloadingCandidates[function + 1])
                # print("CPU:", (
                #                 self.getCPU(
                #                     self.getMem(offloadingCandidates[function + 1])
                #                 )
                #             ))
                # print("DECISION:", (offloadingDecisionsFinal[function + 1][0] / 100))
                # print("VM exe time:", (
                #                 self.getVMexecution(
                #                     offloadingCandidates[function + 1], 0
                #                 )
                #                 * 0.001
                #             ))
                # print("num per req:", self.estimator.get_num_per_req(offloadingCandidates[function + 1], False))
                # print("rps:", self.rps)
                # print("-------")
                # print("Used resources: ", usedResources)

                self.saveNewDecision(offloadingDecisionsFinal)
                return offloadingDecisionsFinal
            except:
                # offloadingDecisionsFinal = [
                #     [0 for i in range(len(availResources))]
                #     for j in range(len(offloadingCandidates))
                # ]
                print("No solution could be found!")
                return "NotFound"
                # self.saveNewDecision(offloadingDecisionsFinal)
                # return offloadingDecisionsFinal
                # model.open_folder()

        elif self.optimizationMode == "latency":
            self.getAllPaths()
            self.getSlackForPath()
            model = GEKKO(remote=False)
            zero = model.Const(0)
            one = model.Const(1)
            alphaConst = model.Const(alpha)
            vms = list(range(len(availResources)))

            tempGoalVar = [
                [
                    model.Var(lb=0, ub=1, integer=True)
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            offloadingDecisions = [
                [
                    model.Var(
                        lb=0,
                        ub=100,
                        integer=True,
                        name=("function:" + str(j) + " resource:" + str(i)),
                    )
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            # Constraint on only having a single or zero one for each vm decision for a function
            for function in offloadingDecisions:
                model.Equation(sum([function[i] for i in range(len(function))]) <= 100)
                # model.Equation( list(function).count(1) <= 1)

            # Constraint on checking available memory of each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            (
                                self.rps
                                * self.estimator.get_num_per_req(
                                    offloadingCandidates[function + 1], False
                                )
                                * (
                                    self.getVMexecution(
                                        offloadingCandidates[function + 1], VMIndex
                                    )
                                    * 0.001
                                )
                                * (offloadingDecisions[function + 1][VMIndex] / 100)
                                * (self.getMem(offloadingCandidates[function + 1]))
                            )
                            for function in range(len(offloadingDecisions) - 1)
                        ]
                    )
                    <= availResources[VMIndex]["mem_mb"]
                )
            # Constraint on checking available number of  cores for each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            (
                                self.rps
                                * self.estimator.get_num_per_req(
                                    offloadingCandidates[function + 1], False
                                )
                                * (
                                    self.getVMexecution(
                                        offloadingCandidates[function + 1], VMIndex
                                    )
                                    * 0.001
                                )
                                * (offloadingDecisions[function + 1][VMIndex] / 100)
                                * self.muFactor
                                # * (
                                #     self.getCPU(
                                #         self.getMem(offloadingCandidates[function + 1])
                                #     )
                                # )
                                # *
                                # 2
                            )
                            for function in range(len(offloadingDecisions) - 1)
                        ]
                    )
                    <= availResources[VMIndex]["cores"]
                )

            # Constraint for showing the first Function should run as serverless
            for i in range(len(offloadingDecisions[0])):
                model.Equation(offloadingDecisions[0][i] == 0)

            for vm in range(len(availResources)):
                for i in range(len(offloadingDecisions)):
                    model.Equation(
                        tempGoalVar[i][vm] == model.min2(offloadingDecisions[i][vm], 1)
                    )

            for duration in self.allPathsSlack:
                path = self.allPathsSlack[duration]
                combinations = list(
                    map(list, itertools.product(vms, repeat=(len(path) - 1)))
                )
                # print("path:  ", path, "  ,combinations:  ", combinations)
                for c in combinations:
                    # print("new combination: ", c)
                    model.Equation(
                        (
                            sum(
                                [
                                    (
                                        tempGoalVar[
                                            self.offloadingCandidates.index(node)
                                        ][c[path.index(node) - 1]]
                                        * (
                                            self.addedExecLatency(
                                                node, c[path.index(node) - 1]
                                            )
                                        )
                                    )
                                    for node in path[1:]
                                ]
                            )
                            + sum(
                                [
                                    (
                                        (
                                            (
                                                tempGoalVar[
                                                    self.offloadingCandidates.index(
                                                        node
                                                    )
                                                ][c[path.index(node) - 1]]
                                            )
                                            * (
                                                tempGoalVar[
                                                    self.offloadingCandidates.index(
                                                        path[path.index(node) + 1]
                                                    )
                                                ][c[path.index(node)]]
                                            )
                                            * self.getCommunicationLatency(
                                                (path[path.index(node) + 1]),
                                                node,
                                                c[path.index(node)],
                                                c[path.index(node) - 1],
                                                self.decisionMode,
                                            )
                                        )
                                        + (
                                            (
                                                1
                                                - (
                                                    tempGoalVar[
                                                        self.offloadingCandidates.index(
                                                            node
                                                        )
                                                    ][c[path.index(node) - 1]]
                                                )
                                            )
                                            * (
                                                tempGoalVar[
                                                    self.offloadingCandidates.index(
                                                        path[path.index(node) + 1]
                                                    )
                                                ][c[path.index(node)]]
                                            )
                                            * self.getCommunicationLatency(
                                                (path[path.index(node) + 1]),
                                                node,
                                                c[path.index(node)],
                                                "s",
                                                self.decisionMode,
                                            )
                                        )
                                        + (
                                            (
                                                tempGoalVar[
                                                    self.offloadingCandidates.index(
                                                        node
                                                    )
                                                ][c[path.index(node) - 1]]
                                            )
                                            * (
                                                1
                                                - (
                                                    tempGoalVar[
                                                        self.offloadingCandidates.index(
                                                            path[path.index(node) + 1]
                                                        )
                                                    ][c[path.index(node)]]
                                                )
                                            )
                                            * self.getCommunicationLatency(
                                                (path[path.index(node) + 1]),
                                                node,
                                                "s",
                                                c[path.index(node) - 1],
                                                self.decisionMode,
                                            )
                                        )
                                    )
                                    for node in path[1:-1]
                                ]
                            )
                            + (
                                (
                                    (
                                        tempGoalVar[
                                            self.offloadingCandidates.index(path[1])
                                        ][c[0]]
                                    )
                                    * self.getCommunicationLatency(
                                        (path[1]),
                                        (path[0]),
                                        c[0],
                                        "s",
                                        self.decisionMode,
                                    )
                                )
                            )
                        )
                        <= (
                            (self.getCriticalPathDuration() - duration)
                            + self.toleranceWindow
                        )
                    )

            model.Minimize(
                model.sum(
                    [
                        (
                            ((10**5) * 2)
                            * (1 - alphaConst)
                            * self.rps
                            * self.estimator.get_num_per_req(
                                offloadingCandidates[i], False
                            )
                            * self.GetServerlessCostEstimate(offloadingCandidates[i])
                            * (
                                (
                                    100
                                    - (
                                        model.sum(
                                            [
                                                (offloadingDecisions[i][vm])
                                                for vm in range(len(availResources))
                                            ]
                                        )
                                    )
                                )
                                # / 100
                            )
                            + (
                                (1 - alphaConst)
                                * self.rps
                                * self.estimator.get_num_per_req(
                                    offloadingCandidates[i], False
                                )
                                * (
                                    self.GetDatastoreCost("w")
                                    + self.GetDatastoreCost("d")
                                    + self.GetDatastoreCost("r")
                                )
                                * (
                                    (
                                        (
                                            model.sum(
                                                [
                                                    (offloadingDecisions[i][vm])
                                                    for vm in range(len(availResources))
                                                ]
                                            )
                                        )
                                    )
                                    / 100
                                )
                            )
                        )
                        + model.sum(
                            [
                                (
                                    # (
                                    #     ((10**5) * 2)
                                    #     * (1 - alphaConst)
                                    #     * (
                                    #         model.sum(
                                    #             [
                                    #                 (
                                    #                     100
                                    #                     - (
                                    #                         (offloadingDecisions[i][vm])
                                    #                         * (
                                    #                             offloadingDecisions[j][
                                    #                                 vm
                                    #                             ]
                                    #                         )
                                    #                         * (0.01)
                                    #                     )
                                    #                 )
                                    #                 * self.rps
                                    #                 *self.estimator.get_num_per_req(offloadingCandidates[i], False)
                                    #                 *self.estimator.get_num_per_req(offloadingCandidates[j], False)
                                    #                 * self.GetPubsubCost(
                                    #                     (offloadingCandidates[i]),
                                    #                     (offloadingCandidates[j]),
                                    #                 )
                                    #                 for j in self.getChildIndexes(
                                    #                     offloadingCandidates[i]
                                    #                 )
                                    #             ]
                                    #         )
                                    #     )
                                    # )
                                    # +
                                    (
                                        (10**3)
                                        * (alphaConst)
                                        * (
                                            model.abs2(
                                                tempGoalVar[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                                for vm in range(len(availResources))
                            ]
                        )
                        for i in range(len(offloadingDecisions))
                    ]
                )
            )
            model.options.SOLVER = 1

            model.options.OTOL = 1e-13
            model.options.RTOL = 1e-13

            try:
                model.solve(disp=False)
                offloadingDecisionsFinal = [
                    [
                        (offloadingDecisions[j][i].value)[0]
                        for i in range(len(availResources))
                    ]
                    for j in range(len(offloadingCandidates))
                ]
                tempGoalVarFinal = [
                    [(tempGoalVar[j][i].value)[0] for i in range(len(availResources))]
                    for j in range(len(offloadingCandidates))
                ]
                cost = sum(
                    [
                        (
                            ((10**5) * 2)
                            * (1 - alpha)
                            * self.rps
                            * self.GetServerlessCostEstimate(offloadingCandidates[i])
                            * (
                                100
                                - (
                                    sum(
                                        [
                                            (offloadingDecisionsFinal[i][vm])
                                            for vm in range(len(availResources))
                                        ]
                                    )
                                )
                            )
                            / 100
                        )
                        + sum(
                            [
                                (
                                    (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (
                                            sum(
                                                [
                                                    # (
                                                    #     max(
                                                    #         (
                                                    #             tempGoalVarFinal[i][vm]
                                                    #             - tempGoalVarFinal[j][
                                                    #                 vm
                                                    #             ]
                                                    #         ),
                                                    #         (
                                                    #             1
                                                    #             - tempGoalVarFinal[i][
                                                    #                 vm
                                                    #             ]
                                                    #         ),
                                                    #     )
                                                    # )
                                                    #                                                (
                                                    #     min(
                                                    #         (
                                                    #             tempGoalVarFinal[i][vm]
                                                    #         ),
                                                    #         (tempGoalVarFinal[j][vm])
                                                    #     )
                                                    # )
                                                    # *(-1)
                                                    # model.if3((-1*(tempGoalVar[i][vm] + tempGoalVar[j][vm])) + 1, zero, one)
                                                    # *
                                                    (
                                                        1
                                                        - (
                                                            (
                                                                offloadingDecisionsFinal[
                                                                    i
                                                                ][
                                                                    vm
                                                                ]
                                                                / 100
                                                            )
                                                            * (
                                                                offloadingDecisionsFinal[
                                                                    j
                                                                ][
                                                                    vm
                                                                ]
                                                                / 100
                                                            )
                                                        )
                                                    )
                                                    * self.rps
                                                    * self.GetPubsubCost(
                                                        (offloadingCandidates[i]),
                                                        (offloadingCandidates[j]),
                                                    )
                                                    for j in self.getChildIndexes(
                                                        offloadingCandidates[i]
                                                    )
                                                ]
                                            )
                                        )
                                    )
                                    + (
                                        (10**3)
                                        * (alpha)
                                        * (
                                            #  max((
                                            #     tempGoalVarFinal[i][vm]
                                            #     - (
                                            #         self.IsOffloaded(
                                            #             offloadingCandidates[i], vm
                                            #         )
                                            #     )), (
                                            #      (
                                            #         self.IsOffloaded(
                                            #             offloadingCandidates[i], vm
                                            #         )
                                            #     ) - tempGoalVarFinal[i][vm])
                                            # )
                                            abs(
                                                tempGoalVarFinal[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                        # (
                                        #     abs(
                                        #         tempGoalVarFinal[i][vm]
                                        #         - (
                                        #             self.IsOffloaded(
                                        #                 offloadingCandidates[i], vm
                                        #             )
                                        #         )
                                        #     )
                                        # )
                                    )
                                )
                                for vm in range(len(availResources))
                            ]
                        )
                        for i in range(len(offloadingDecisionsFinal))
                    ]
                )
                cost1 = sum(
                    [
                        (
                            ((10**5) * 2)
                            * (1 - alpha)
                            * self.rps
                            * self.GetServerlessCostEstimate(offloadingCandidates[i])
                            * (
                                100
                                - (
                                    sum(
                                        [
                                            (offloadingDecisionsFinal[i][vm])
                                            for vm in range(len(availResources))
                                        ]
                                    )
                                )
                            )
                            / 100
                        )
                        for i in range(len(offloadingDecisionsFinal))
                    ]
                )
                cost2 = sum(
                    [
                        sum(
                            [
                                (
                                    (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (
                                            sum(
                                                [
                                                    # (
                                                    #     max(
                                                    #         (
                                                    #             tempGoalVarFinal[i][vm]
                                                    #             - tempGoalVarFinal[j][
                                                    #                 vm
                                                    #             ]
                                                    #         ),
                                                    #         (
                                                    #             1
                                                    #             - tempGoalVarFinal[i][
                                                    #                 vm
                                                    #             ]
                                                    #         ),
                                                    #     )
                                                    # )
                                                    #                                                (
                                                    #     min(
                                                    #         (
                                                    #             tempGoalVarFinal[i][vm]
                                                    #         ),
                                                    #         (tempGoalVarFinal[j][vm])
                                                    #     )
                                                    # )
                                                    # # model.if3((-1*(tempGoalVar[i][vm] + tempGoalVar[j][vm])) + 1, zero, one)
                                                    # *(-1)
                                                    # model.if3((-1*(tempGoalVar[i][vm] + tempGoalVar[j][vm])) + 1, zero, one)
                                                    # *
                                                    (
                                                        1
                                                        - (
                                                            (
                                                                offloadingDecisionsFinal[
                                                                    i
                                                                ][
                                                                    vm
                                                                ]
                                                                / 100
                                                            )
                                                            * (
                                                                offloadingDecisionsFinal[
                                                                    j
                                                                ][
                                                                    vm
                                                                ]
                                                                / 100
                                                            )
                                                        )
                                                    )
                                                    * self.rps
                                                    * self.GetPubsubCost(
                                                        (offloadingCandidates[i]),
                                                        (offloadingCandidates[j]),
                                                    )
                                                    for j in self.getChildIndexes(
                                                        offloadingCandidates[i]
                                                    )
                                                ]
                                            )
                                        )
                                    )
                                )
                                for vm in range(len(availResources))
                            ]
                        )
                        for i in range(len(offloadingDecisionsFinal))
                    ]
                )
                cost3 = sum(
                    [
                        sum(
                            [
                                (
                                    (
                                        (10**3)
                                        * (alpha)
                                        * (
                                            #  max((
                                            #     tempGoalVarFinal[i][vm]
                                            #     - (
                                            #         self.IsOffloaded(
                                            #             offloadingCandidates[i], vm
                                            #         )
                                            #     )), (
                                            #      (
                                            #         self.IsOffloaded(
                                            #             offloadingCandidates[i], vm
                                            #         )
                                            #     ) - tempGoalVarFinal[i][vm])
                                            # )
                                            abs(
                                                tempGoalVarFinal[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                        # (
                                        #     abs(
                                        #         tempGoalVarFinal[i][vm]
                                        #         - (
                                        #             self.IsOffloaded(
                                        #                 offloadingCandidates[i], vm
                                        #             )
                                        #         )
                                        #     )
                                        # )
                                    )
                                )
                                for vm in range(len(availResources))
                            ]
                        )
                        for i in range(len(offloadingDecisionsFinal))
                    ]
                )

                #     AddedLatency = sum([ ((sum([ ((offloadingDecisions[node]*self.allPathsSlack[path][node]*(self.addedExecLatency(offloadingCandidates[node]))) + ((sum([((self.allPathsSlack[path])[node])*(abs(offloadingDecisions[node]-offloadingDecisions[j]))*self.addedComLatency((offloadingCandidates[j]), (offloadingCandidates[node])) for j in self.getParentIndexes(offloadingCandidates[node])])))) for node in range(len(x))]) ))  for path in self.allPathsSlack])
                self.saveNewDecision(offloadingDecisionsFinal)
                # , cost1, cost2, cost3
                # return (
                #     tempGoalVarFinal,
                #     offloadingDecisionsFinal,
                #     cost,
                #     cost1,
                #     cost2,
                #     cost3,
                # )
                return offloadingDecisionsFinal
            except:
                # offloadingDecisionsFinal = [
                #     [0 for i in range(len(availResources))]
                #     for j in range(len(offloadingCandidates))
                # ]
                print("No solution could be found!")
                # self.saveNewDecision(offloadingDecisionsFinal)
                # return offloadingDecisionsFinal, 0, 0, 0, 0, 0
                # return offloadingDecisionsFinal
                return "NotFound"
                # model.open_folder()

    # Saving new decisions in the Json file assigned to each workflow
    def saveNewDecision(self, offloadingDecisions):
        self.workflow_json[
            "lastDecision" + "_" + self.decisionMode
        ] = offloadingDecisions
        with open(self.jsonPath, "w") as json_file:
            json.dump(self.workflow_json, json_file)


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    # workflow = "TestCase2Workflow"
    workflow = "Text2SpeechCensoringWorkflow"
    mode = "cost"
    toleranceWindow = 0
    solver = rpsOffloadingSolver(workflow, mode, "default", toleranceWindow, 1.4, 0)
    # availResources =  [{'cores':100, 'mem_mb':10000}]
    availResources = [{"cores": 3, "mem_mb": 2000}]
    verbose = True
    alpha = 0
    # x, cost, latency = solver.suggestBestOffloadingSingleVM(availResources, alpha, verbose)
    vm = solver.suggestBestOffloadingMultiVM(availResources, alpha, verbose)
    # print("X:{}".format(x))
    print("VMDECISIONS:{}".format(vm))
