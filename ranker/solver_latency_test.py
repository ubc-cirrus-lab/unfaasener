import unittest
from solver import Solver
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
        solver = Solver(None, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 0
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_highCost(self):
        path = path = os.getcwd()+ "/test/data/"+self.workflow +", "+self.mode+","+"highCost"+".csv"
        solver = Solver(path, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_highPubsubCost(self):
        path = os.getcwd()+ "/test/data/"+self.workflow +", "+self.mode+", "+"highPubSubCost"+".csv"
        solver = Solver(path, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_limitedVMresources(self):
        solver = Solver(None, self.workflow, self.mode)
        availResources =  {'cores':1000, 'mem_mb':500000}
        alpha = 1
        x = solver.suggestBestOffloadingSingleVM(availResources=availResources, alpha=alpha, verbose=True)
        self.assertEqual(x, [0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

if __name__ == '__main__':
    unittest.main()

