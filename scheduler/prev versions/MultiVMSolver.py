import os
import json
import string
from unicodedata import name
import pandas as pd
import numpy as np
from pathlib import Path
from LatencyModel import LatencyModel
from gekko import GEKKO
from Estimator import Estimator

# Non-linear optimzation models for cost and latency


class OffloadingSolver:
    def __init__(self, workflow, mode, decisionMode, toleranceWindow):
        with open(
            ((os.path.dirname(os.path.abspath(__file__))) + "/data/" + str(workflow) + "/" + "slackData.json"), "r"
        ) as outfile:
            self.slacksDF = json.load(outfile)
        with open(
            ((os.path.dirname(os.path.abspath(__file__))) + "/data/" + str(workflow) + "/" + "slackDurations.json"), "r"
        ) as outfile:
            self.slackDurationsDF = json.load(outfile)
        with open(
            ((os.path.dirname(os.path.abspath(__file__)))+ "/data/" + str(workflow) + "/" + "pubSubSize.json"), "r"
        ) as outfile:
            self.pubSubSize = json.load(outfile)
        with open(
            ((os.path.dirname(os.path.abspath(__file__))) + "/data/" + str(workflow) + "/" + "Costs.json"), "r"
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
            boolArray = [0] * len(self.offloadingCandidates)
            for node in path:
                boolArray[self.offloadingCandidates.index(node)] = 1
            self.allPaths.append(boolArray)

    def getDuration(self, func):
        """
        Returns estimated duration for each function based on the dataframe
        """
        duration = self.slackDurationsDF[func][self.decisionMode]
        # duration = (self.dataframe.loc[self.dataframe['function'] == func, 'duration'].item())
        return duration

    def getCriticalPathDuration(self):
        """
        Returns estimated duration for the critical path
        """
        durations = list(self.allPathsSlack.keys())
        cpDuration = max(durations)
        return cpDuration

    def getSlackForPath(self):
        """
        Returns a list consists of all paths in the workflow besides their duration as a dictionary
        """
        for path in self.allPaths:
            nodes = []
            comNodes = []
            duration = 0
            for offloadingCandidate in self.offloadingCandidates:
                if path[self.offloadingCandidates.index(offloadingCandidate)] == 1:
                    nodes.append(offloadingCandidate)
            for s in nodes:
                for child in self.successors[self.offloadingCandidates.index(s)]:
                    if child in nodes:
                        comNodes.append(s + "-" + child)

            nodes = nodes + comNodes
            for node in nodes:
                duration += self.getDuration(node)
            self.allPathsSlack[duration] = path

    def addedExecLatency(self, offloadingCandidate, vm):
        """
        Returns estimated added execution time which is caused by offloading a serverless function to VM
        """
        # vmDF = self.VMdataframe[vm]
        # serverless = self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'duration'].item()
        # vm = vmDF.loc[vmDF['function'] == offloadingCandidate, 'duration'].item()
        serverless = self.estimator.getFuncExecutionTime(
            offloadingCandidate, "s", self.decisionMode
        )
        vm = self.estimator.getFuncExecutionTime(
            offloadingCandidate, ("vm" + str(vm)), self.decisionMode
        )
        diff = vm - serverless
        return diff

    # Function for added end-to-end latency by offloading a function to VM
    # ......TO-DO: Change this function in order to find added communication latency based on real data
    def addedComLatency(self, parent, child):
        """
        Returns estimated added end-to-end latency by offloading a function to VM
        """
        latencyModel = LatencyModel()
        # msgSize = float(self.dataframe.loc[self.dataframe['function'] == (parent+"-"+child), 'PubsubMessageSize(Bytes)'].item())
        # msgSize = self.estimator.getPubSubSize(child)
        msgSize = self.pubSubSize[child]
        latency = latencyModel.getLinearAddedLatency(msgSize)
        return latency

    def getMem(self, offloadingCandidate):
        """
        Returns required memory for the function based on the dataframe
        """
        mem = self.memories[self.offloadingCandidates.index(offloadingCandidate)]
        mem = mem * 1000
        # mem = float(self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'Memory(GB)'].item()) * 1000
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
        # cost = self.estimator.getFuncCost(self.decisionMode, offloadingCandidate)
        # cost = (self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'cost'].item())
        return cost

    def IsOffloaded(self, offloadingCandidate, vm):
        """
        Returns previous offloadind decision for the function
        """
        decision = self.lastDecision[
            self.offloadingCandidates.index(offloadingCandidate)
        ][vm]
        return decision

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

    def GetPubsubCost(self, offloadingCandidate, child):
        """
        Returns estimated pub/sub cost based on the dataframe
        """
        # cost = self.estimator.getPubSubCost(child)
        cost = self.estimator.getComCost(self.pubSubSize[child])
        # cost = (self.dataframe.loc[self.dataframe['function'] == (offloadingCandidate+"-"+child), 'cost'].item())
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
            offloadingDecisions = [
                [
                    model.Var(
                        lb=0,
                        ub=1,
                        integer=True,
                        name=("function:" + str(j) + " resource:" + str(i)),
                    )
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            # Constraint on only having a single or zero one for each vm decision for a function
            for function in offloadingDecisions:
                model.Equation(sum([function[i] for i in range(len(function))]) <= 1)
                # model.Equation( list(function).count(1) <= 1)

            # Constraint on checking available memory of each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            offloadingDecisions[function][VMIndex]
                            * self.getMem(offloadingCandidates[function])
                            for function in range(len(offloadingDecisions))
                        ]
                    )
                    <= availResources[VMIndex]["mem_mb"]
                )
            # Constraint on checking available number of  cores for each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            offloadingDecisions[function][VMIndex]
                            * self.getCPU(self.getMem(offloadingCandidates[function]))
                            for function in range(len(offloadingDecisions))
                        ]
                    )
                    <= availResources[VMIndex]["cores"]
                )

            # Constraint for showing the first Function should run as serverless
            for i in range(len(offloadingDecisions[0])):
                model.Equation(offloadingDecisions[0][i] == 0)

            model.Minimize(
                model.sum(
                    [
                        model.sum(
                            [
                                (
                                    (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (1 - offloadingDecisions[i][vm])
                                        * (
                                            self.GetServerlessCostEstimate(
                                                offloadingCandidates[i]
                                            )
                                        )
                                    )
                                    + (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (
                                            model.sum(
                                                [
                                                    model.max2(
                                                        (
                                                            1
                                                            - (
                                                                offloadingDecisions[i][
                                                                    vm
                                                                ]
                                                                + offloadingDecisions[
                                                                    j
                                                                ][vm]
                                                            )
                                                        ),
                                                        model.abs2(
                                                            offloadingDecisions[i][vm]
                                                            - offloadingDecisions[j][vm]
                                                        ),
                                                    )
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
                                        (alpha)
                                        * (
                                            model.abs2(
                                                offloadingDecisions[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                                for i in range(len(offloadingDecisions))
                            ]
                        )
                        for vm in range(len(availResources))
                    ]
                )
            )

            # solve
            model.options.SOLVER = 1
            try:
                model.solve()
                offloadingDecisionsFinal = [
                    [
                        (offloadingDecisions[j][i].value)[0]
                        for i in range(len(availResources))
                    ]
                    for j in range(len(offloadingCandidates))
                ]
                self.saveNewDecision(offloadingDecisionsFinal)
                return offloadingDecisionsFinal
            except:
                print("No solution could be found!")
                model.open_folder()

        elif self.optimizationMode == "latency":
            # self.getSlacks()
            # self.getPaths()
            self.getAllPaths()
            self.getSlackForPath()
            model = GEKKO(remote=False)
            # List of functions as the variables
            offloadingDecisions = [
                [
                    model.Var(lb=0, ub=1, integer=True)
                    for i in range(len(availResources))
                ]
                for j in range(len(offloadingCandidates))
            ]

            # Constraint on only having a single or zero one for each vm decision for a function
            for function in offloadingDecisions:
                model.Equation(sum([function[i] for i in range(len(function))]) <= 1)
                # model.Equation( list(function).count(1) <= 1)

            # Constraint on checking available memory of each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            offloadingDecisions[function][VMIndex]
                            * self.getMem(offloadingCandidates[function])
                            for function in range(len(offloadingDecisions))
                        ]
                    )
                    <= availResources[VMIndex]["mem_mb"]
                )
            # Constraint on checking available number of  cores for each VM
            for VMIndex in range(len(availResources)):
                model.Equation(
                    sum(
                        [
                            offloadingDecisions[function][VMIndex]
                            * self.getCPU(self.getMem(offloadingCandidates[function]))
                            for function in range(len(offloadingDecisions))
                        ]
                    )
                    <= availResources[VMIndex]["cores"]
                )

            # Constraint for showing the first Function should run as serverless
            for i in range(len(offloadingDecisions[0])):
                model.Equation(offloadingDecisions[0][i] == 0)

            # Constraint on checking slack time for each Node
            for vm in range(len(availResources)):
                for path in self.allPathsSlack:
                    model.Equation(
                        
                                sum(
                                    [
                                        (
                                            (
                                                offloadingDecisions[node + 1][vm]
                                                * self.allPathsSlack[path][node + 1]
                                                * (
                                                    self.addedExecLatency(
                                                        offloadingCandidates[node + 1], vm
                                                    )
                                                )
                                            )
                                            + (
                                                (
                                                    sum(
                                                        [
                                                            (
                                                                (self.allPathsSlack[path])[
                                                                    node + 1
                                                                ]
                                                            )
                                                            * (
                                                                model.abs2(
                                                                    offloadingDecisions[
                                                                        node + 1
                                                                    ][vm]
                                                                    - offloadingDecisions[
                                                                        j
                                                                    ][vm]
                                                                )
                                                            )
                                                            * (
                                                                (self.allPathsSlack[path])[
                                                                    j
                                                                ]
                                                            )
                                                            * self.addedComLatency(
                                                                (offloadingCandidates[j]),
                                                                (
                                                                    offloadingCandidates[
                                                                        node + 1
                                                                    ]
                                                                ),
                                                            )
                                                            for j in self.getParentIndexes(
                                                                offloadingCandidates[node + 1]
                                                            )
                                                        ]
                                                    )
                                                )
                                            )
                                        )
                                        for node in range(len(offloadingDecisions) - 1)
                                    ]

                        )
                        <= ((self.getCriticalPathDuration() - path) + self.toleranceWindow)
                    )

            # # Constraint on checking the toleranceWindow
            # model.Equation( sum([ (sum ([sum([ ((offloadingDecisions[node][vm]*self.allPathsSlack[path][node]*(self.addedExecLatency(offloadingCandidates[node], vm))) + ((sum([((self.allPathsSlack[path])[node])*(model.abs2(offloadingDecisions[node][vm]-offloadingDecisions[j][vm]))*((self.allPathsSlack[path])[j])*self.addedComLatency((offloadingCandidates[j]), (offloadingCandidates[node])) for j in self.getParentIndexes(offloadingCandidates[node])])))) for node in range(len(offloadingDecisions))]) for vm in range(len(availResources))]) - (self.getCriticalPathDuration() - path))  for path in self.allPathsSlack])  <= self.toleranceWindow)

            # optimization goal

            model.Minimize(
                model.sum(
                    [
                        model.sum(
                            [
                                (
                                    (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (1 - offloadingDecisions[i][vm])
                                        * (
                                            self.GetServerlessCostEstimate(
                                                offloadingCandidates[i]
                                            )
                                        )
                                    )
                                    + (
                                        ((10**5) * 2)
                                        * (1 - alpha)
                                        * (
                                            model.sum(
                                                [
                                                    model.max2(
                                                        (
                                                            1
                                                            - (
                                                                offloadingDecisions[i][
                                                                    vm
                                                                ]
                                                                + offloadingDecisions[
                                                                    j
                                                                ][vm]
                                                            )
                                                        ),
                                                        model.abs2(
                                                            offloadingDecisions[i][vm]
                                                            - offloadingDecisions[j][vm]
                                                        ),
                                                    )
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
                                        (alpha)
                                        * (
                                            model.abs2(
                                                offloadingDecisions[i][vm]
                                                - (
                                                    self.IsOffloaded(
                                                        offloadingCandidates[i], vm
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                                for i in range(len(offloadingDecisions))
                            ]
                        )
                        for vm in range(len(availResources))
                    ]
                )
            )

            model.options.SOLVER = 1

            try:
                model.solve()
                offloadingDecisionsFinal = [
                    [
                        (offloadingDecisions[j][i].value)[0]
                        for i in range(len(availResources))
                    ]
                    for j in range(len(offloadingCandidates))
                ]

                #     cost = sum( [(((10**5)*2)*(1-alpha)*(1 - offloadingDecisions[i])*(self.GetServerlessCostEstimate(offloadingCandidates[i])) + \
                # (((10**5)*2)*(1-alpha)*sum([max((1- (offloadingDecisions[i]+offloadingDecisions[j])), abs(offloadingDecisions[i] - offloadingDecisions[j]))*self.GetPubsubCost((offloadingCandidates[i]), (offloadingCandidates[j])) for j in self.getChildIndexes(offloadingCandidates[i])])) +  ((alpha)*(abs(offloadingDecisions[i] - (self.IsOffloaded(offloadingCandidates[i])) )))) \
                #                                 for i in range(len(x))] )

                #     AddedLatency = sum([ ((sum([ ((offloadingDecisions[node]*self.allPathsSlack[path][node]*(self.addedExecLatency(offloadingCandidates[node]))) + ((sum([((self.allPathsSlack[path])[node])*(abs(offloadingDecisions[node]-offloadingDecisions[j]))*self.addedComLatency((offloadingCandidates[j]), (offloadingCandidates[node])) for j in self.getParentIndexes(offloadingCandidates[node])])))) for node in range(len(x))]) ))  for path in self.allPathsSlack])
                self.saveNewDecision(offloadingDecisionsFinal)
                return offloadingDecisionsFinal
            except:
                print("No solution could be found!")
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
    workflow = "TestCase2Workflow"
    # workflow = "Text2SpeechCensoringWorkflow"
    mode = "latency"
    toleranceWindow = 260
    solver = OffloadingSolver(workflow, mode, None, toleranceWindow)
    # availResources =  [{'cores':100, 'mem_mb':10000}]
    availResources = [{"cores": 20, "mem_mb": 2000}]
    verbose = True
    alpha = 0
    # x, cost, latency = solver.suggestBestOffloadingSingleVM(availResources, alpha, verbose)
    vm = solver.suggestBestOffloadingMultiVM(availResources, alpha, verbose)
    # print("X:{}".format(x))
    print("VMDECISIONS:{}".format(vm))
