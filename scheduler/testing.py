import unittest
from MultiVMSolver import OffloadingSolver
from tabnanny import verbose
from mip import *
import os
import json
import pandas as pd
from pathlib import Path
from CIScheduler import CIScheduler
from rpsMultiVMSolver import rpsOffloadingSolver

rpss = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 20, 25, 30, 50, 100]
# rpss = [2, 5, 10]
for rps in rpss:
    mode = "latency"
    workflow = "TestCase11Workflow"
    toleranceWindow = 50
    jsonPath = (
        str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        + "/log_parser/get_workflow_logs/data/"
        + "TestCase11Workflow"
        + ".json"
    )
    with open(jsonPath, "r") as json_file:
        workflow_json = json.load(json_file)
    workflow_json["lastDecision_default"] = [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0]
        # [0.0, 0.0],
        # [0.0, 0.0]
        # [0.0, 0.0]
    ]
    with open(jsonPath, "w") as json_file:
        json.dump(workflow_json, json_file)
    solver = rpsOffloadingSolver(
        workflow=workflow,
        mode=mode,
        decisionMode=None,
        toleranceWindow=toleranceWindow,
        rps=rps,
    )
    availResources = [
        {"cores": 2, "mem_mb": 400},
        # {"cores": 1, "mem_mb": 100}
        # {"cores": 10, "mem_mb": 9000},
        # {"cores": 2, "mem_mb": 400}
    ]
    alpha = 0
    temp, x, cost, cost1, cost2, cost3 = solver.suggestBestOffloadingMultiVM(
        availResources=availResources, alpha=alpha, verbose=True
    )
    with open("testing.txt", "a") as f:
        f.write("-----------------")
        f.write("\n")
        f.write(
            "rps::"
            + str(rps)
            + ", Cost: "
            + str(cost)
            + ", Cost1: "
            + str(cost1)
            + ", Cost2: "
            + str(cost2)
            + ", Cost3: "
            + str(cost3)
        )
        # f.write("rps::"+ str(rps) + ", Cost: " +  str(cost))
        f.write("\n")
        # f.write("temp: " + str(temp))
        # f.write('\n')
        f.write("Decision: " + str(x))
        f.write("\n")
    # print("CostFunctionnnds: ", cost)
    # print("Decision: ", x)
