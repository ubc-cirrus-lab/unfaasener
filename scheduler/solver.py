import math
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path


class OffloadingSolver:

    def __init__(self, dataframePath, vmDataframePath, workflow, mode, decisionMode, toleranceWindow):
###############################
        self.baseLatencyVM = 1
        self.baseLatencyServerless = 1
        self.thVM = 1
        self.thServerless = 1
###############################
        self.VMdataframe = None
        self.slacks = {}
        self.terminals = []
        self.allPaths = []
        self.dataframePath = dataframePath
        self.decisionMode = decisionMode
        if self.decisionMode == None:
             self.decisionMode = "default"
        self.addedLatency = 30
        self.toleranceWindow = toleranceWindow
        self.GCP_MB2GHz = {128:0.2, 256:0.4, 512:0.8, 1000:1.4, 2000:2.4, 4000:4.8, 8000:4.8}
        if dataframePath == None:
            dataframePath = (os.getcwd()+ "/data/"+workflow +", "+mode+", "+self.decisionMode+",CSV-slackData.csv")
        self.jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + workflow+".json"
        if dataframePath.endswith(".pkl"):
            self.dataframe = pd.read_pickle(dataframePath)
        elif dataframePath.endswith(".csv"):
            self.dataframe = pd.read_csv(dataframePath)

        if vmDataframePath == None:
            vmDataframePath = (os.getcwd()+ "/data/"+"VM,"+workflow +", "+mode+", "+self.decisionMode+",CSV-slackData.csv")
        if vmDataframePath.endswith(".pkl"):
            self.VMdataframe = pd.read_pickle(vmDataframePath)
        elif vmDataframePath.endswith(".csv"):
            self.VMdataframe = pd.read_csv(vmDataframePath)


        with open(self.jsonPath, 'r') as json_file:
            self.workflow_json = json.load(json_file)
        self.optimizationMode = mode
        self.offloadingCandidates = self.workflow_json["workflowFunctions"]
        self.lastDecision = self.workflow_json["lastDecision"]
        self.successors = self.workflow_json["successors"]
        self.predecessors = self.workflow_json["predecessors"]
        self.initial = self.workflow_json["initFunc"]
        self.paths = {}
   


    def getAllPaths(self):
        """
        Returns all possible paths in the dag starting from the initial node to a terminal node
        """
        terminals = []
        for node in self.offloadingCandidates:
            if len(self.successors[ self.offloadingCandidates.index(node) ]) == 0:
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
                for successor in self.successors[ self.offloadingCandidates.index(lastNode) ]:
                    new_path = path.copy()
                    new_path.append(successor)
                    queue.append(new_path)
                visited.add(tuple(path))
        for path in results:
            boolArray = [0]*len(self.offloadingCandidates)
            for node in path:
                boolArray[self.offloadingCandidates.index(node)] = 1
            self.allPaths.append(boolArray)



    def checkNeighbour(self, node, neighbour):
        """
        - node, neighbour: nodes to be checked
        Returns 0 if the two functions are not in the same path
        Returns 1 ifthe two functions are in the same path
        """
        if self.slacks[self.offloadingCandidates[node]] == 0:
            if node == neighbour:
                return 1
            else:
                return 0
        else:
            for path in self.allPaths:
                if (path[node] == 1) and (path[neighbour] == 1):
                    return 1
        return 0


    def getSlacks(self):
        """
        Returns estimated slack time for each function based on the dataframe
        """
        for func in self.offloadingCandidates:
            self.slacks[func] = (self.dataframe.loc[self.dataframe['function'] == func, 'slackTime'].item())

    # Function for added execution time by offloading a function to VM
    def addedExecLatency(self, offloadingCandidate):
        """
        Returns estimated added execution time which is caused by offloading a serverless function to VM
        """
        serverless = self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'duration'].item()
        vm = self.VMdataframe.loc[self.VMdataframe['function'] == offloadingCandidate, 'duration'].item()
        diff = vm - serverless
        return diff

    # Function for added end-to-end latency by offloading a function to VM
    def addedComLatency(self, parent, child):
        """
        Returns estimated added end-to-end latency by offloading a function to VM
        """
        msgSize = float(self.dataframe.loc[self.dataframe['function'] == (child+"-"+parent), 'PubsubMessageSize(Bytes)'].item())
        latency = (self.baseLatencyVM - self.baseLatencyServerless) + msgSize*((1/self.thVM) - (1/self.thServerless))
        return latency


    # Function for getting Paths with the same slack time
    def getPaths(self):
        """
        Returns a list of dictionaries, showing slacktime as the key and a list of binary values showing if a function belongs to that path or not
        """
        for func in self.offloadingCandidates:
            slack = (self.dataframe.loc[self.dataframe['function'] == func, 'slackTime'].item())
            if slack in self.paths.keys():
                self.paths[slack][self.offloadingCandidates.index(func)]  = 1
            else:
                self.paths[slack] = [0]*len(self.offloadingCandidates)
                self.paths[slack][self.offloadingCandidates.index(func)]  = 1

    def getMem(self, offloadingCandidate):
        """
        Returns required memory for the function based on the dataframe
        """
        mem = float(self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'Memory(GB)'].item()) * 1000
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
        cost = (self.dataframe.loc[self.dataframe['function'] == offloadingCandidate, 'cost'].item())
        return cost

    def IsOffloaded(self,offloadingCandidate):
        """
        Returns previous offloadind decision for the function
        """
        decision = self.lastDecision[ self.offloadingCandidates.index(offloadingCandidate) ]
        return decision


    def onCriticalPath(self, offloadingCandidate):
        """
        Returns a boolean value(0:The function is on the critical path, 1: The function is not on the critical path)
        - offloadingCandidate: function we needed to check
        """
        cp = self.paths[0][ self.offloadingCandidates.index(offloadingCandidate) ]
        return cp
    
    def checkOnPath(self, offloadingCandidate, path):
        """
        Returns a boolean value(0:The function is on a specified path, 1: The function is not on a specified path)
        - offloadingCandidate: function we needed to check
        - path: path to check 
        """
        check = self.paths[path][ self.offloadingCandidates.index(offloadingCandidate) ]
        return check

    def cutomizedAbs(self, secondTerm):
        """
        Returns an integer to multiply whenever we need abs for a subtraction of two binary variables
        - secondTerm: second term in the subtraction
        """
        if secondTerm == 0:
            return 1
        else:
            return -1


    def customizedFunc(self, first, second):
        if first == 1 :
            if second == 0:
                return 1
            else:
                return 0
        else:
            return 0
            
    def getChildIndexes(self, offloadingCandidate):
        """
        Returns indexes for the children of a function based on sucessors
        """
        childrenIndexes = []
        children = self.successors[ self.offloadingCandidates.index(offloadingCandidate) ]
        for child in children:
            childrenIndexes.append(self.offloadingCandidates.index(child))
        return  childrenIndexes

    def getParentIndexes(self, offloadingCandidate):
        """
        Returns indexes for the children of a function based on sucessors
        """
        childrenIndexes = []
        children = self.successors[ self.offloadingCandidates.index(offloadingCandidate) ]
        for child in children:
            childrenIndexes.append(self.offloadingCandidates.index(child))
        return  childrenIndexes

    def GetPubsubCost(self, offloadingCandidate, child):
        """
        Returns estimated pub/sub cost based on the dataframe
        """
        cost = (self.dataframe.loc[self.dataframe['function'] == (offloadingCandidate+"-"+child), 'cost'].item())
        return cost



    def suggestBestOffloadingSingleVM(self, availResources, alpha, verbose):
        """
        Returns a list of 0's (no offloading) and 1's (offloading)
        - optimizationMode: "cost"   or   "latency"
        - offloadingCandidates: list of function objects
        - availResources: {'cores':C, 'mem_mb':M}
        - alpha: FP number in [0, 1]
        """
        offloadingCandidates = self.offloadingCandidates
        if self.optimizationMode == "cost":
            model = Model(sense=MINIMIZE, solver_name=CBC)

            # List of functions as the variables
            x = [model.add_var(name=s, var_type=BINARY) for s in offloadingCandidates]

            # optimization goal
            model.objective = xsum( [1000*alpha*(1 - x[i])*(self.GetServerlessCostEstimate(offloadingCandidates[i])) + \
                                    xsum([1000*alpha*(x[i] - x[j])*self.cutomizedAbs(x[j])*self.GetPubsubCost((offloadingCandidates[i]), (offloadingCandidates[j])) for j in self.getChildIndexes(offloadingCandidates[i])]) + \
                                (1 - alpha)*((x[i] - (self.IsOffloaded(offloadingCandidates[i])) )*self.cutomizedAbs(self.IsOffloaded(offloadingCandidates[i]))) \
                                    for i in range(len(x))] )

           

            # Constraint for showing the first Function should run as serverless
            model.add_constr( x[0] == 0,
                                priority=1)
            # Memory constraint
            model.add_constr( xsum( [x[i]*self.getMem(offloadingCandidates[i]) \
                                for i in range(len(x))] ) <= availResources['mem_mb'],
                                priority=1)
            # CPU constraint
            model.add_constr( xsum( [x[i]*self.getCPU( self.getMem( offloadingCandidates[i] ) ) \
                                for i in range(len(x))] ) <= availResources['cores'],
                                priority=1)


            # solve
            status = model.optimize(max_seconds=30)
            if verbose:
                print(status)
            if [x[i].x for i in range(len(x))] == [None for i in range(len(x))]:
                print("No solution could be found!")

        elif self.optimizationMode == "latency":
            self.getSlacks()
            self.getPaths()
            self.getAllPaths()
            model = Model(sense=MINIMIZE, solver_name=CBC)
            # List of functions as the variables
            x = [model.add_var(var_type=BINARY, name = s) for s in offloadingCandidates]
            
            # optimization goal
            model.objective = xsum( [1000*alpha*(1 - x[i])*(self.GetServerlessCostEstimate(offloadingCandidates[i])) + \
                                    xsum([1000*alpha*(x[i] - x[j])*self.cutomizedAbs(x[j])*self.GetPubsubCost((offloadingCandidates[i]), (offloadingCandidates[j])) for j in self.getChildIndexes(offloadingCandidates[i])]) + \
                                (1 - alpha)*((x[i] - (self.IsOffloaded(offloadingCandidates[i])) )*self.cutomizedAbs(self.IsOffloaded(offloadingCandidates[i]))) \
                                    for i in range(len(x))] )
            # Constraint for showing the first Function should run as serverless
            model.add_constr( x[0] == 0,
                                priority=1)
            # Memory constraint
            model.add_constr( xsum( [x[i]*self.getMem(offloadingCandidates[i]) \
                                for i in range(len(x))] ) <= availResources['mem_mb'],
                                priority=1)
            # CPU constraint
            model.add_constr( xsum( [x[i]*self.getCPU( self.getMem( offloadingCandidates[i] ) ) \
                                for i in range(len(x))] ) <= availResources['cores'],
                                priority=1)

            # Constraint on checking slack time for each Node
            for node in range(len(x)):
                model.add_constr( xsum( [x[neighbour]*self.checkNeighbour(node, neighbour)*((self.addedExecLatency(offloadingCandidates[neighbour])) )+ (self.checkNeighbour(node, neighbour)*(xsum([(x[neighbour] - x[j])*self.customizedFunc(x[neighbour], x[j])*self.addedComLatency((offloadingCandidates[j]), (offloadingCandidates[neighbour])) for j in self.getParentIndexes(offloadingCandidates[neighbour])])) )\
                for neighbour in range(len(x))] ) <= self.slacks[offloadingCandidates[node]] + self.toleranceWindow,
                priority=1)

            # Constraint on checking the toleranceWindow
            model.add_constr(xsum( [ (xsum( [x[neighbour]*self.checkNeighbour(node, neighbour)*((self.addedExecLatency(offloadingCandidates[neighbour])) )+ (self.checkNeighbour(node, neighbour)*(xsum([(x[neighbour] - x[j])*self.customizedFunc(x[neighbour], x[j])*self.addedComLatency((offloadingCandidates[j]), (offloadingCandidates[neighbour])) for j in self.getParentIndexes(offloadingCandidates[neighbour])])) ) \
            for neighbour in range(len(x))] ) - self.slacks[offloadingCandidates[node]]) for node in range(len(x))] )<= self.toleranceWindow, priority=1)

            # solve
            status = model.optimize(max_seconds=30)
            if verbose:
                print(status)
            if [x[i].x for i in range(len(x))] == [None for i in range(len(x))]:
                print("No solution could be found!")
        else:
            print("Invalid optimization mode!")
            return [0 for i in range(len(offloadingCandidates))]

        offloadingDecisions = [x[i].x for i in range(len(x))]
        # self.saveNewDecision(offloadingDecisions)

        return offloadingDecisions

    # Saving new decisions in the Json file assigned to each workflow
    def saveNewDecision(self, offloadingDecisions):
        self.workflow_json["lastDecision"] = offloadingDecisions
        with open(self.jsonPath, 'w') as json_file:
            json.dump(self.workflow_json, json_file)



if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    workflow = "Text2SpeechCensoringWorkflow"
    # mode = "cost"
    mode = "latency"
    # path = "/Users/ghazal/Desktop/UBC/Research/de-serverlessization/ranker/test/data/Text2SpeechCensoringWorkflow, latency, highPubSubCost.csv"
    # path = "/Users/ghazal/Desktop/UBC/Research/de-serverlessization/ranker/test/data/Text2SpeechCensoringWorkflow, cost, highCost.csv"
    # solver = OffloadingSolver(None, workflow, mode)
    toleranceWindow = 0
    solver = OffloadingSolver(None,None, workflow, mode, None, toleranceWindow)
    availResources =  {'cores':1000, 'mem_mb':500000}
    verbose = True
    alpha = 1
    x = solver.suggestBestOffloadingSingleVM(availResources, alpha, verbose)
    print(x)
