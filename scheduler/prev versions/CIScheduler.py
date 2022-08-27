from MultiVMSolver import OffloadingSolver
# import rankerConfig
import configparser
import time
import numpy as np
import sys
import os
import json
from pathlib import Path
from google.cloud import datastore
from baselineSlackAnalysis import baselineSlackAnalysis
from Estimator import Estimator 


class CIScheduler:
    def __init__(self):
        path = str(Path(os.path.dirname(os.path.abspath(__file__))))+"/rankerConfig.ini"
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.workflow = self.rankerConfig["workflow"]
        slack = baselineSlackAnalysis(self.workflow)
        x = Estimator(self.workflow)
        x.getCost()
        x.getPubSubMessageSize()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key/schedulerKey.json"
        project = "ubc-serverless-ghazal"
        self.datastore_client = datastore.Client()
        kind = "routingDecision"
        name = self.workflow
        routing_key = self.datastore_client.key(kind, name)
        self.routing = self.datastore_client.get(key=routing_key)
        self.decisionModes = (self.rankerConfig["decisionMode"]).split()
        self.mode = self.rankerConfig["mode"]
        self.alpha = float(self.rankerConfig["statisticalParameter"])
        resources = open('resources.txt', 'r')
        Lines = resources.readlines()
        cpus = Lines[0].split()
        memories = Lines[1].split()
        self.availableResources = []
        assert len(cpus) == len(memories), "Both number of cores and memory should be provided for each VM"
        for i in range(len(cpus)):
            dict = {}
            dict["cores"] = float(cpus[i])
            dict["mem_mb"] = float(memories[i])
            self.availableResources.append(dict)
        print("AvailableResources ===", self.availableResources)
        # self.availableResources = rankerConfig.availResources
        self.toleranceWindow = int(self.rankerConfig["toleranceWindow"])
        self.suggestBestOffloadingMultiVM()


    def suggestBestOffloadingMultiVM(self):
        decisions = []
        for decisionMode in self.decisionModes:
            solver = OffloadingSolver(
                self.workflow, self.mode, decisionMode, self.toleranceWindow
            )
            x = solver.suggestBestOffloadingMultiVM(
                availResources=self.availableResources, alpha=self.alpha, verbose=True
            )
            decisions.append(x)
        finalDecision = [[0] * len(decisions[0][0])] * len(decisions[0])
        for decision in decisions:
            finalDecision = np.add(finalDecision, decision)
        finalDecision = finalDecision / len(decisions)
        finalDecision = np.where(finalDecision == 1, 0.9, finalDecision)
        finalDecision = list(finalDecision)
        for function in range(len(finalDecision)):
            finalDecision[function] = list(finalDecision[function])
        self.routing["routing"] = str(finalDecision)
        self.datastore_client.put(self.routing)
        print("Final Decision: {}".format(list(finalDecision)))


if __name__ == "__main__":
    # jsonPath = (
    #     str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #     + "/log_parser/get_workflow_logs/data/"
    #     + "Text2SpeechCensoringWorkflow"
    #     + ".json"
    # )
    # with open(jsonPath, "r") as json_file:
    #     workflow_json = json.load(json_file)
    # workflow_json["lastDecision_default"] = [
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    # ]
    # workflow_json["lastDecision_best-case"] = [
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    # ]
    # workflow_json["lastDecision_worst-case"] = [
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    #     [0.0, 0.0, 0.0],
    # ]
    # with open(jsonPath, "w") as json_file:
    #     json.dump(workflow_json, json_file)
    start_time = time.time()
    solver = CIScheduler()
    print("--- %s seconds ---" % (time.time() - start_time))