import unittest
from MINLPSolver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path
from CIScheduler import CIScheduler

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
        toleranceWindow = 0
        solver = OffloadingSolver(None, None, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on the decision when there is a high cost for serverless functions
    def test_highCost(self):
        workflow = "Text2SpeechCensoringWorkflow"
        path  = os.getcwd()+ "/test/data/"+workflow +", "+self.mode+","+"highCost"+".csv"
        toleranceWindow = 0
        solver = OffloadingSolver(path, None, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    
    # Test on the decision when there is a high cost on pub/sub communication between functions
    def test_highPubsubCost(self):
        workflow = "Text2SpeechCensoringWorkflow"
        path = os.getcwd()+ "/test/data/"+workflow +", "+self.mode+", "+"highPubSubCost"+".csv"
        toleranceWindow = 0
        solver = OffloadingSolver(path, None, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on the decision when there is not enough resources for offloading on the VM side
    def test_limitedVMresources(self):
        workflow = "Text2SpeechCensoringWorkflow"
        toleranceWindow = 0
        solver = OffloadingSolver(None, None, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':0, 'mem_mb':0}
        alpha = 0

        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Test on checking the paths with the same slack time
    def test_sameSlackTime(self):
        workflow = "TestWorkflow"
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "TestWorkflow"+".json"
        path = os.getcwd()+ "/test/data/"+workflow +", SameSlackForPaths.csv"
        vmPath = os.getcwd()+ "/test/data/"+"VM-"+workflow +", SameSlackForPaths.csv"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        toleranceWindow = 0
        solver = OffloadingSolver(path,vmPath, workflow, self.mode,  None,toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    
    # Test for checking the reduction in the nodes in the same path but with different slack time    
    def test_diffPaths(self):
        print("test_diffPaths")
        workflow = "TestWorkflow"
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "TestWorkflow"+".json"
        path = os.getcwd()+ "/test/data/"+workflow +".csv"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        vmPath = os.getcwd()+ "/test/data/"+"VM-"+workflow +".csv"
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        toleranceWindow = 0
        solver = OffloadingSolver(path,vmPath, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0])
    
    # Test for checking the toleranceWindow 
    def test_toleranceWindow(self):
        print("test_toleranceWindow")
        workflow = "TestWorkflow"
        jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "TestWorkflow"+".json"
        path = os.getcwd()+ "/test/data/"+workflow +".csv"
        vmPath = os.getcwd()+ "/test/data/"+"VM-"+workflow +".csv"
        with open(jsonPath, 'r') as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(jsonPath, 'w') as json_file:
            json.dump(workflow_json, json_file)
        toleranceWindow = 35
        solver = OffloadingSolver(path,vmPath, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    
    # Test on when the tolerance window is not limited for the user
    def test_unlimitedToleranceWindow(self):
        workflow = "Text2SpeechCensoringWorkflow"
        path  = os.getcwd()+ "/test/data/"+workflow +", "+self.mode+","+"highCost"+".csv"
        toleranceWindow = 1000000
        solver = OffloadingSolver(path, None, workflow, self.mode, None, toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x, _, _ = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    def test_confidenctInterval(self):
        print("test_confidenctInterval")
        workflow = "TestWorkflow"
        mode = "latency"
        toleranceWindow = 0
        solver = CIScheduler(workflow, mode,toleranceWindow)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x= solver.suggestBestOffloadingSingleVM(availResources, alpha)
        self.assertEqual(x, [0.0, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.9, 0.6666666666666666, 0.3333333333333333, 0.9, 0.6666666666666666])



if __name__ == '__main__':
    unittest.main()

