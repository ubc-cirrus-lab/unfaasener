import unittest
from MINLPSolver import OffloadingSolver
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
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=None, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = {"cores": 1000, "mem_mb": 500000}
        alpha = 1
        x, _ = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_highPubsubCost(self):
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
        availResources = {"cores": 1000, "mem_mb": 500000}
        alpha = 0
        x, _ = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    def test_highCost(self):
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
        availResources = {"cores": 1000, "mem_mb": 500000}
        alpha = 0
        x, _ = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

    def test_limitedVMresources(self):
        toleranceWindow = 0
        solver = OffloadingSolver(
            dataframePath=None, vmDataframePath= None, workflow=self.workflow, mode=self.mode, decisionMode=None, toleranceWindow=toleranceWindow
        )
        availResources = {"cores": 0, "mem_mb": 0}
        alpha = 0
        x, _ = solver.suggestBestOffloadingSingleVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        self.assertEqual(x, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])


if __name__ == "__main__":
    jsonPath = (
        str(Path(os.getcwd()).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "Text2SpeechCensoringWorkflow"
        + ".json"
    )
    with open(jsonPath, "r") as json_file:
        workflow_json = json.load(json_file)
    workflow_json["lastDecision"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    with open(jsonPath, "w") as json_file:
        json.dump(workflow_json, json_file)
    unittest.main()
