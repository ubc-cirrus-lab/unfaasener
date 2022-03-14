import unittest
from solver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path

class TestSolver(unittest.TestCase):
    
    workflow = "Text2SpeechCensoringWorkflow"
    mode = "latency"


    def test_similar2prevdecision(self):
        solver = OffloadingSolver(None, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_highCost(self):
        path  = os.getcwd()+ "/test/data/"+self.workflow +", "+self.mode+","+"highCost"+".csv"
        solver = OffloadingSolver(path, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_highPubsubCost(self):
        path = os.getcwd()+ "/test/data/"+self.workflow +", "+self.mode+", "+"highPubSubCost"+".csv"
        solver = OffloadingSolver(path, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_limitedVMresources(self):
        solver = OffloadingSolver(None, self.workflow, self.mode)
        availResources =  {'cores':0, 'mem_mb':0}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

if __name__ == '__main__':
    jsonPath = str(Path(os.getcwd()).resolve().parents[0]) + "/log_parser/get_workflow_logs/data/" + "Text2SpeechCensoringWorkflow"+".json"
    with open(jsonPath, 'r') as json_file:
        workflow_json = json.load(json_file)
    workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    with open(jsonPath, 'w') as json_file:
        json.dump(workflow_json, json_file)
    unittest.main()

