import unittest
from multipleVMSolver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path


class TestSolver(unittest.TestCase):

    workflow = "Text2SpeechCensoringWorkflow"
    mode = "cost"

    def test_similar2prevdecision(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=None, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

    def test_highPubsubCost(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        path = (
            os.getcwd()
            + "/test/data/"
            + self.workflow
            + ", "
            + self.mode
            + ", "
            + "highPubSubCost"
            + ".csv"
        )
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=path, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [1.0], [1.0], [1.0], [1.0], [1.0], [1.0]])

    def test_highCost(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        path = (
            os.getcwd()
            + "/test/data/"
            + self.workflow
            + ", "
            + self.mode
            + ","
            + "highCost"
            + ".csv"
        )
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=path, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [1.0], [1.0], [1.0], [1.0], [1.0], [1.0]])

    def test_limitedVMresources(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=None, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 0, "mem_mb": 0}]
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

    def test_multipleVMs_chooseTwoMostCostlyFuncs(self):
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "Text2SpeechCensoringWorkflow"+".json"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        workflow = "Text2SpeechCensoringWorkflow"
        toleranceWindow = 0
        solver = OffloadingSolver(None, None, workflow, self.mode, None, toleranceWindow)
        availResources =  [{'cores':0.4, 'mem_mb':256}, {'cores':0.4, 'mem_mb':256}, {'cores':0, 'mem_mb':0}]
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    
    def test_multipleVMs_preferLocality(self):
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "Text2SpeechCensoringWorkflow"+".json"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        workflow = "Text2SpeechCensoringWorkflow"
        toleranceWindow = 0
        solver = OffloadingSolver(None, None, workflow, self.mode, None, toleranceWindow)
        availResources =  [{'cores':4.4, 'mem_mb':3536}, {'cores':1, 'mem_mb':500}, {'cores':0, 'mem_mb':0}]
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

if __name__ == "__main__":
    unittest.main()
