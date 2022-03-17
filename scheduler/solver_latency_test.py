import unittest
from solver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path

class TestSolver(unittest.TestCase):
    mode = "latency"


    def test_similar2prevdecision(self):
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "Text2SpeechCensoringWorkflow"+".json"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        workflow = "Text2SpeechCensoringWorkflow"
        solver = OffloadingSolver(None,workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on the decision when there is a high cost for serverless functions
    def test_highCost(self):
        workflow = "Text2SpeechCensoringWorkflow"
        path  = os.getcwd()+ "/test/data/"+workflow +", "+self.mode+","+"highCost"+".csv"
        solver = OffloadingSolver(path, workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on the decision when there is a high cost on pub/sub communication between functions
    def test_highPubsubCost(self):
        workflow = "Text2SpeechCensoringWorkflow"
        path = os.getcwd()+ "/test/data/"+workflow +", "+self.mode+", "+"highPubSubCost"+".csv"
        solver = OffloadingSolver(path, workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on the decision when there is not enough resources for offloading on the VM side
    def test_limitedVMresources(self):
        workflow = "Text2SpeechCensoringWorkflow"
        solver = OffloadingSolver(None, workflow, self.mode)
        availResources =  {'cores':0, 'mem_mb':0}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on checking the paths with the same slack time
    def test_sameSlackTime(self):
        workflow = "TestWorkflow"
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "TestWorkflow"+".json"
        path = os.getcwd()+ "/test/data/"+workflow +", SameSlackForPaths.csv"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        solver = OffloadingSolver(path,workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    
    # Test for checking the reduction in the nodes in the same path but with different slack time    
    def test_diffPaths(self):
        workflow = "TestWorkflow"
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "TestWorkflow"+".json"
        path = os.getcwd()+ "/test/data/"+workflow +".csv"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        solver = OffloadingSolver(path,workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0])



if __name__ == '__main__':
    unittest.main()

