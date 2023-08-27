import unittest
from mip import *
import os
import json
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
            + "/log-parser/get-workflow-logs/data/"
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
            testingFlag=True,
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 1
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        expected = [[0.0], [0.0], [0.0], [0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    def test_preferHigherCost(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 200
        solver = rpsOffloadingSolver(
            workflow=workflow,
            mode=self.mode,
            decisionMode=None,
            toleranceWindow=toleranceWindow,
            rps=self.rps,
            testingFlag=True,
        )
        availResources = [{"cores": 1, "mem_mb": 500}]
        alpha = 0
        # Due to the change of adding mu factor set to 1, the cpu for that function is increased causing the change in decisions
        expected = [[0.0], [0.0], [52.0], [0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        #self.assertEqual(x, [[0.0], [0.0], [52.0], [0.0]])

    # Test on when the tolerance window is not limited for the user
    def test_unlimitedToleranceWindow(self):
        workflow = "TestCase2Workflow"
        toleranceWindow = 100000000
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag=True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        expected = [[0.0], [100.0], [100.0], [100.0], [100.0], [100.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0], [100.0], [100.0], [100.0], [100.0], [100.0]])

    # Test for checking the case which the toleranceWindow is more than what is required for offloading a function
    def test_giveReuiredtoleranceWindow1(self):
        workflow = "TestCase11Workflow"
        toleranceWindow = 50
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag=True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        expected = [[0.0], [100.0], [0.0], [0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0], [100.0], [0.0], [0.0]])
        # Test for checking the case which the toleranceWindow is less than what is required for offloading a function

    def test_lessThanrequiredtoleranceWindow(self):
        workflow = "TestCase11Workflow"
        toleranceWindow = 20
        solver = rpsOffloadingSolver(
            workflow, self.mode, None, toleranceWindow, rps=self.rps, testingFlag=True
        )
        availResources = [{"cores": 1000, "mem_mb": 500000}]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        expected = [[0.0], [0.0], [0.0], [0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    def test_rps(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 200
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
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
            testingFlag=True,
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
        expected = [[0.0, 0.0], [0.0, 0.0], [79.0, 21.0], [0.0, 0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0, 0.0], [0.0, 0.0], [79.0, 21.0], [0.0, 0.0]])

    def test_rps2(self):
        workflow = "TestCase3Workflow"
        toleranceWindow = 160
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
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
            testingFlag=True,
        )
        availResources = [
            {"cores": 2, "mem_mb": 100},
        ]
        alpha = 0
        x = solver.suggestBestOffloadingMultiVM(
            availResources=availResources, alpha=alpha, verbose=True
        )
        expected = [[0.0], [0.0], [21.0], [0.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0], [0.0], [21.0], [0.0]])

    def test_rps3(self):
        workflow = "TestCase10Workflow"
        toleranceWindow = 300
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
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
            testingFlag=True,
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
        expected = [[0.0, 0.0], [0.0, 0.0], [84.0, 16.0], [0.0, 5.0]]
        cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
        print(f'EXPECTED = {expected}')
        print(f'COST EXPECTED = {cost_expected}')
        gekko_result = solver.suggestBestOffloadingMultiVMGekko(
            availResources=availResources, alpha=alpha, verbose=True
        )
        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
        print(f'GEKKO = {gekko_result}')
        print(f'COST GEKKO = {cost_gekko}')
        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x)
        print(f'Julia = {x}')
        print(f'COST Julia = {cost_julia}')
        print('-----------------------------------')
        self.assertAlmostEqual(cost_gekko, cost_julia, delta=0.1*cost_gekko)
        # print('-----------------------------------')
        # self.assertEqual(x, [[0.0, 0.0], [0.0, 0.0], [84.0, 16.0], [0.0, 5.0]])

    # def test_confidenctInterval(self):
    #     print("test_confidenctInterval")
    #     workflow = "TestCase2Workflow"
    #     toleranceWindow = 0
    #     solver = CIScheduler(workflow, self.mode, toleranceWindow)
    #     availResources =  [{'cores':1000, 'mem_mb':500000}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(availResources, alpha)
    # expected = [[0.0], [0.0], [0.9], [0.0], [0.9], [0.9]]
    # cost_expected = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, expected)
    # print(f'EXPECTED = {expected}')
    # # print(f'COST EXPECTED = {cost_expected}')
    # gekko_result = solver.suggestBestOffloadingMultiVMGekko(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    # cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, gekko_result)
    # print(f'GEKKO = {gekko_result}')
    # print(f'COST GEKKO = {cost_gekko}')
    # print('-----------------------------------')
    #     self.assertEqual(x, [[0.0], [0.0], [0.9], [0.0], [0.9], [0.9]])


if __name__ == "__main__":
    unittest.main()
