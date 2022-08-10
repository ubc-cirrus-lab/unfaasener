import rankerConfig
import time
import numpy as np
import sys
import os
import json
from pathlib import Path
from google.cloud import datastore
from baselineSlackAnalysis import baselineSlackAnalysis
from rpsMultiVMSolver import rpsOffloadingSolver
from Estimator import Estimator
from getInvocationRate import InvocationRate
import sys


class CIScheduler:
    def __init__(self, triggerType):
        self.workflow = rankerConfig.workflow
        slack = baselineSlackAnalysis(self.workflow)
        x = Estimator(self.workflow)
        self.invocationRate = InvocationRate(self.workflow)
        # self.rates = invocationRate.getRPS()
        x.getCost()
        x.getPubSubMessageSize()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key/schedulerKey.json"
        project = "ubc-serverless-ghazal"
        self.datastore_client = datastore.Client()
        kind = "routingDecision"
        name = self.workflow
        routing_key = self.datastore_client.key(kind, name)
        self.routing = self.datastore_client.get(key=routing_key)
        self.decisionModes = rankerConfig.decisionMode
        self.mode = rankerConfig.mode
        self.alpha = rankerConfig.statisticalParameter
        self.rps = rankerConfig.rps
        resources = open("resources.txt", "r")
        Lines = resources.readlines()
        cpus = Lines[0].split()
        memories = Lines[1].split()
        self.availableResources = []
        assert len(cpus) == len(
            memories
        ), "Both number of cores and memory should be provided for each VM"
        for i in range(len(cpus)):
            dict = {}
            dict["cores"] = float(cpus[i])
            dict["mem_mb"] = float(memories[i])
            self.availableResources.append(dict)
        print("AvailableResources ===", self.availableResources)
        # self.availableResources = rankerConfig.availResources
        self.toleranceWindow = rankerConfig.toleranceWindow
        self.suggestBestOffloadingMultiVM(triggerType)

    def suggestBestOffloadingMultiVM(self, triggerType):
        if triggerType == "highLoad":
            prevPercentage = self.routing["active"]
            match prevPercentage:
                case "25":
                    self.routing["active"] = "50"
                    self.datastore_client.put(self.routing)
                case "50":
                    self.routing["active"] = "75"
                    self.datastore_client.put(self.routing)
                case "75":
                    self.routing["active"] = "95"
                    self.datastore_client.put(self.routing)
                case "95":
                    self.resolveOffloadingSolutions()
                case other:
                    print("Unknown percentile")
        elif triggerType == "lowLoad":
            prevPercentage = self.routing["active"]
            match prevPercentage:
                case "95":
                    self.routing["active"] = "75"
                    self.datastore_client.put(self.routing)
                case "75":
                    self.routing["active"] = "50"
                    self.datastore_client.put(self.routing)
                case "50":
                    self.routing["active"] = "25"
                    self.datastore_client.put(self.routing)
                case "25":
                    self.resolveOffloadingSolutions()
                case other:
                    print("Unknown percentile")
        elif triggerType == "resolve":
            self.resolveOffloadingSolutions()
        else:
            print("Unknown trigger type!")

    def resolveOffloadingSolutions(self):
        rates = self.invocationRate.getRPS()
        decisions = []
        for percent in rates.keys():
            rate = rates[percent]
            for decisionMode in self.decisionModes:
                solver = rpsOffloadingSolver(
                    self.workflow, self.mode, decisionMode, self.toleranceWindow, rate, False
                )
                x = solver.suggestBestOffloadingMultiVM(
                    availResources=self.availableResources,
                    alpha=self.alpha,
                    verbose=True,
                )
                print("Decision for case: {}:{}".format(decisionMode, x))
                decisions.append(x)
            # finalDecision = [[0] * len(decisions[0][0])] * len(decisions[0])
            # for decision in decisions:
            #     finalDecision = np.add(finalDecision, decision)
            finalDecision = np.mean(decisions, axis=0)
            finalDecision = finalDecision / 100
            capArray = np.zeros(len(finalDecision))
            for i in range(len(capArray)):
                capArray[i] = np.full(len(finalDecision[i]), 0.9)
                finalDecision[i] = np.minimum(finalDecision[i], capArray[i])
            # finalDecision = np.where(finalDecision == 1, 0.9, finalDecision)
            finalDecision = list(finalDecision)
            for function in range(len(finalDecision)):
                finalDecision[function] = list(finalDecision[function])
            self.routing["routing" + "_" + str(percent)] = str(finalDecision)
            print("Final Decision: {}".format(list(finalDecision)))
        self.routing["active"] = "50"
        self.datastore_client.put(self.routing)


if __name__ == "__main__":
    start_time = time.time()
    # triggerType = "resolve"
    triggerType = sys.argv[1]
    solver = CIScheduler(triggerType)
    print("--- %s seconds ---" % (time.time() - start_time))
