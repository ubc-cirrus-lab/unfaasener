import unittest
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path
from rpsMultiVMSolver import rpsOffloadingSolver


class TestSolver(unittest.TestCase):
    mode = "latency"
    rps = 10

    def test_similar2prevdecision(self):
        workflow = "TestCase3Workflow"
        toleranceWindow = 0
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + "TestCase3Workflow"
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag = True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 1
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    def test_preferHigherCost(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 200
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag = True
        )
        availResources = [{"cores": 1, "mem_mb": 500}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [100.0], [0.0]])

    # Test on when the tolerance window is not limited for the user
    def test_unlimitedToleranceWindow(self):
        workflow = "TestCase2Workflow"
        toleranceWindow = 100000000
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag = True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [100.0], [100.0], [100.0], [100.0], [100.0]])

    # Test for checking the case which the toleranceWindow is more than what is required for offloading a function
    def test_giveReuiredtoleranceWindow1(self):
        workflow = "TestCase11Workflow"
        toleranceWindow = 50
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag = True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [100.0], [0.0], [0.0]])
        # Test for checking the case which the toleranceWindow is less than what is required for offloading a function

    def test_lessThanrequiredtoleranceWindow(self):
        workflow = "TestCase11Workflow"
        toleranceWindow = 20
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag = True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    def test_rps(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 200
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + "TestCase10Workflow"
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag = True
        )
        availResources = [
            {"cores": 2, "mem_mb": 400},
            {"cores": 1, "mem_mb": 100}
            # {"cores": 10, "mem_mb": 9000},
            # {"cores": 2, "mem_mb": 400}
            # {"cores": 2, "mem_mb": 600},
            # {"cores": 2, "mem_mb": 400}
        ]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0, 0.0], [0.0, 0.0], [79.0, 21.0], [0.0, 0.0]])

    def test_rps2(self):
        workflow = "TestCase3Workflow"
        toleranceWindow = 160
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + "TestCase3Workflow"
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag = True
        )
        availResources = [
            {"cores": 2, "mem_mb": 100},
        ]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0], [0.0], [21.0], [0.0]])

    def test_rps3(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 300
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + "TestCase10Workflow"
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        workflow_json["lastDecision_default"] = [
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ]
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag = True
        )
        availResources = [
            {"cores": 2, "mem_mb": 400},
            {"cores": 1, "mem_mb": 100}
            # {"cores": 10, "mem_mb": 9000},
            # {"cores": 2, "mem_mb": 400}
            # {"cores": 2, "mem_mb": 600},
            # {"cores": 2, "mem_mb": 400}
        ]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [[0.0, 0.0], [0.0, 0.0], [84.0, 16.0], [0.0, 5.0]])

    # def test_confidenctInterval(self):
    #     print("test_confidenctInterval")
    #     workflow = "TestCase2Workflow"
    #     toleranceWindow = 0
    #     solver = CIScheduler(workflow, self.mode, toleranceWindow)
    #     availResources =  [{'cores':1000, 'mem_mb':500000}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(availResources, alpha)
    #     self.assertEqual(x, [[0.0], [0.0], [0.9], [0.0], [0.9], [0.9]])


if __name__ == "__main__":
    unittest.main()
