from MultiVMSolver import OffloadingSolver
import rankerConfig
import time
import numpy as np
import os
import json
from pathlib import Path
from google.cloud import datastore


class CIScheduler:
    def __init__(self, workflow, mode, toleranceWindow):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key/schedulerKey.json"
        project = "ubc-serverless-ghazal"
        self.datastore_client = datastore.Client()
        kind = "routingDecision"
        name = workflow
        routing_key = self.datastore_client.key(kind, name)
        self.routing = self.datastore_client.get(key=routing_key)
        self.decisionModes = rankerConfig.decisionMode
        self.workflow = workflow
        self.mode = mode
        self.toleranceWindow = toleranceWindow

    def suggestBestOffloadingSingleVM(self, availResources, alpha):
        decisions = []
        for decisionMode in self.decisionModes:
            solver = OffloadingSolver(
                self.workflow, self.mode, decisionMode, self.toleranceWindow
            )
            x = solver.suggestBestOffloadingMultiVM(
                availResources=availResources, alpha=alpha, verbose=True
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
        return list(finalDecision)


if __name__ == "__main__":
    jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
    )
    with open(jsonPath, "r") as json_file:
        workflow_json = json.load(json_file)
    workflow_json["lastDecision_default"] = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    workflow_json["lastDecision_best-case"] = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    workflow_json["lastDecision_worst-case"] = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    with open(jsonPath, "w") as json_file:
        json.dump(workflow_json, json_file)
    workflow = "Text2SpeechCensoringWorkflow"
    mode = "cost"
    toleranceWindow = 0
    start_time = time.time()
    solver = CIScheduler(workflow, mode, toleranceWindow)
    availResources = [
        {"cores": 4.4, "mem_mb": 3536},
        {"cores": 1, "mem_mb": 500},
        {"cores": 0, "mem_mb": 0},
    ]
    alpha = 0
    x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha)
    print("Final Decision: {}".format(x))
    print("--- %s seconds ---" % (time.time() - start_time))
