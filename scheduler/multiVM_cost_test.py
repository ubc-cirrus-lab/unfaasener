import unittest
from MultiVMSolver import OffloadingSolver
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
            workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 1
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

    def test_highPubsubCost(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "TestCaseWorkflow"
        + ".json"
        )
        workflow = "TestCaseWorkflow"
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        highPubsubSize = {"A": 10e10, "B": 10e10, "C": 10e10, "D": 10e10}
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'pubSubSize.json'), "r") as json_file:
            prevPubSubSize = json.load(json_file)
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'pubSubSize.json'), 'w') as outfile:
            json.dump(highPubsubSize, outfile) 
        toleranceWindow = 0
        solver = OffloadingSolver(
            workflow=workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'pubSubSize.json'), 'w') as outfile:
            json.dump(prevPubSubSize, outfile) 
        self.assertEqual(x, [[0.0], [1.0], [1.0], [1.0]])
        


    def test_highCost(self):
        jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "TestCaseWorkflow"
        + ".json"
        )
        workflow = "TestCaseWorkflow"
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'Costs.json'), "r") as json_file:
            prevCosts = json.load(json_file)
        highCost = prevCosts
        for func in highCost.keys():
            highCost[func]["default"] = 10e10
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'Costs.json'), 'w') as outfile:
            json.dump(highCost, outfile) 
        toleranceWindow = 0
        solver = OffloadingSolver(
            workflow=workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        with open((os.getcwd()+"/data/" + str(workflow)+ "/"+'Costs.json'), 'w') as outfile:
            json.dump(prevCosts, outfile)
        self.assertEqual(x, [[0.0], [1.0], [1.0], [1.0]])
        
    def test_limitedVMResources(self):
        toleranceWindow = 0
        solver = OffloadingSolver(
            workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = [{"cores": 0, "mem_mb": 0}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
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
        solver = OffloadingSolver(workflow, self.mode, None, toleranceWindow)
        availResources =  [{'cores':0.4, 'mem_mb':256}, {'cores':0.4, 'mem_mb':256}, {'cores':0, 'mem_mb':0}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(availResources=availResources, alpha=alpha, verbose=True)
        print("RESS:::",x)
        self.assertIn(x, [[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]])
    




if __name__ == "__main__":
    unittest.main()
