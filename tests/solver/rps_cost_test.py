import unittest
import os
import json
from pathlib import Path
import pandas as pd
import random
import time
import numpy as np
from rpsMultiVMSolver import rpsOffloadingSolver

class TestCaseGenerator:
    def __init__(self, n_funcs, n_hosts):
        self.n_funcs = n_funcs
        self.n_hosts = n_hosts
        random.seed(0)

    def build(self):
        log_data = []

        for i in range(self.n_funcs):
            for id in range(10):
                log_data.append({
                    'function': f'Func_{i}',
                    'reqID': id,
                    'start': "",
                    'finish': "",
                    'mergingPoint': "",
                    'host': "s",
                    'duration': 100
                })

        for j in range(self.n_hosts):
            for i in range(self.n_funcs):
                for id in range(10):
                    log_data.append({
                        'function': f'Func_{i}',
                        'reqID': id,
                        'start': "",
                        'finish': "",
                        'mergingPoint': "",
                        'host': f"vm{j}",
                        'duration': 100
                    })

        df = pd.DataFrame(log_data)
        df.to_csv('../log-parser/get-workflow-logs/data/TestCaseNWorkflow/generatedDataFrame.csv')
        #df.to_csv('/home/pjavan/unfaasener/tests/logCollector/TestCaseNWorkflow/generatedDataFrame.csv')
        
        costs_dict = {}
        pubSub_dict = {}
        slack_data = {}

        successors = []
        predecessors = []
        workflowFunctions = []
        last_dec = []
        
        for i in range(self.n_funcs):
            func_name = f'Func_{i}'
            workflowFunctions.append(func_name)
            # if i == 1:
            #     costs_dict[func_name] = {"best-case": 10000, "worst-case": 10000, "default": 10000}
            # elif i == 2:
            #     costs_dict[func_name] = {"best-case": 10000, "worst-case": 10000, "default": 10000}
            # elif i == 3:
            #     costs_dict[func_name] = {"best-case": 10000, "worst-case": 10000, "default": 10000}
            # elif i == 4:
            #     costs_dict[func_name] = {"best-case": 10000, "worst-case": 10000, "default": 10000}
            # else:                
            #     costs_dict[func_name] = {"best-case": 4.6399999999999997e-07, "worst-case": 4.6399999999999997e-07, "default": 4.6399999999999997e-07}
            
            costs_dict[func_name] = {"best-case": 4.6399999999999997e-07, "worst-case": 4.6399999999999997e-07, "default": 4.6399999999999997e-07}
            
            pubSub_dict[func_name] = 100000000000
            slack_data[func_name] = {"best-case": 0.0, "worst-case": 0.0, "default": 0.0}
            if i < self.n_funcs-1:
                slack_data[f'Func_{i}-Func_{i+1}'] = {"best-case": 0.0, "worst-case": 0.0, "default": 0.0}
                successors.append([f'Func_{i+1}'])
            else: successors.append([])

            if i > 0: predecessors.append([f'Func_{i-1}'])
            else: predecessors.append([])

            if random.randint(1, 10) > 5:
                dec = []
                
                for vm in range(self.n_hosts):
                    if random.randint(1, 10) > 5:
                        dec.append(1.0)
                    else:
                        dec.append(0.0)

                last_dec.append(dec)
            else:
                last_dec.append([0.0]*self.n_hosts)



        workflow_dict = {
            "workflow": "TestCaseNWorkflow", 
            "workflowFunctions": workflowFunctions, 
            "initFunc": "Func_0", 
            "successors": successors, 
            "predecessors": predecessors, 
            "memory": [1/self.n_funcs]*self.n_funcs,
            "lastDecision_default": last_dec,
            "lastDecision_best-case": last_dec,
            "lastDecision_worst-case": last_dec,
            "topics": [""] + ["dag-Profanity"]*(self.n_funcs-1)
        }

        jsonPath = (
            "../log-parser/get-workflow-logs/data/"
            + "TestCaseNWorkflow"
            + ".json"
        )
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_dict, json_file)


        base_dir = './data/TestCaseNWorkflow'
        
        with open(f"{base_dir}/Costs.json", "w") as outfile:
            json.dump(costs_dict, outfile)

        with open(f"{base_dir}/pubSubSize.json", "w") as outfile:
            json.dump(pubSub_dict, outfile)

        with open(f"{base_dir}/slackData.json", "w") as outfile:
            json.dump(slack_data, outfile)

        with open(f"{base_dir}/slackDurations.json", "w") as outfile:
            json.dump(slack_data, outfile)

    def delete(self):
        base_dir = './data/TestCaseNWorkflow'
        os.system('rm ../log-parser/get-workflow-logs/data/TestCaseNWorkflow/generatedDataFrame.csv')
        os.system(f"rm {base_dir}/Costs.json")
        os.system(f"rm {base_dir}/pubSubSize.json")
        os.system(f"rm {base_dir}/slackData.json")
        os.system(f"rm {base_dir}/slackDurations.json")
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + "TestCaseNWorkflow"
            + ".json"
        )
        os.system(f"rm {jsonPath}")


class TestSolver(unittest.TestCase):

    workflow = "Text2SpeechCensoringWorkflow"
    mode = "cost"
    rps = 10

    # def test_similar2prevdecision(self):
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCase3Workflow"
    #         + ".json"
    #     )
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     toleranceWindow = 0
    #     solver = rpsOffloadingSolver(
    #         workflow="TestCase3Workflow",
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [{"cores": 1000, "mem_mb": 500000}]
    #     alpha = 1
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )

    #     self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    # def test_highPubsubCost(self):
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCaseWorkflow"
    #         + ".json"
    #     )
    #     workflow = "TestCaseWorkflow"
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     highPubsubSize = {"A": 10e10, "B": 10e10, "C": 10e10, "D": 10e10}
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "pubSubSize.json"
    #         ),
    #         "r",
    #     ) as json_file:
    #         prevPubSubSize = json.load(json_file)
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "pubSubSize.json"
    #         ),
    #         "w",
    #     ) as outfile:
    #         json.dump(highPubsubSize, outfile)
    #     toleranceWindow = 0
    #     solver = rpsOffloadingSolver(
    #         workflow=workflow,
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [{"cores": 1000, "mem_mb": 500000}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "pubSubSize.json"
    #         ),
    #         "w",
    #     ) as outfile:
    #         json.dump(prevPubSubSize, outfile)
    #     self.assertEqual(x, [[0.0], [100.0], [100.0], [100.0]])

    # def test_highCost(self):
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCaseWorkflow"
    #         + ".json"
    #     )
    #     workflow = "TestCaseWorkflow"
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [[0.0], [0.0], [0.0], [0.0]]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "Costs.json"
    #         ),
    #         "r",
    #     ) as json_file:
    #         prevCosts = json.load(json_file)
    #     highCost = prevCosts.copy()
    #     for func in highCost.keys():
    #         highCost[func]["default"] = 10e10
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "Costs.json"
    #         ),
    #         "w",
    #     ) as outfile:
    #         json.dump(highCost, outfile)
    #     toleranceWindow = 0
    #     solver = rpsOffloadingSolver(
    #         workflow=workflow,
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [{"cores": 1000, "mem_mb": 500000}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     with open(
    #         (
    #             (os.path.dirname(os.path.abspath(__file__)))
    #             + "/data/"
    #             + str(workflow)
    #             + "/"
    #             + "Costs.json"
    #         ),
    #         "w",
    #     ) as outfile:
    #         json.dump(prevCosts, outfile)
    #     self.assertEqual(x, [[0.0], [100.0], [100.0], [100.0]])

    # def test_limitedVMResources(self):
    #     toleranceWindow = 0
    #     solver = rpsOffloadingSolver(
    #         workflow="TestCaseWorkflow",
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [{"cores": 0, "mem_mb": 0}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     self.assertEqual(x, [[0.0], [0.0], [0.0], [0.0]])

    # def test_rps(self):
    #     workflow = "TestCase3Workflow"
    #     toleranceWindow = 0
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCase3Workflow"
    #         + ".json"
    #     )
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #     ]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     solver = rpsOffloadingSolver(
    #         workflow=workflow,
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [
    #         {"cores": 1, "mem_mb": 300},
    #         {"cores": 1, "mem_mb": 300},
    #     ]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     self.assertIn(
    #         x,
    #         [
    #             #  Due to adding the mu factor set to 1 by default the decisions have changed
    #             [[0.0, 0.0], [1.0, 0.0], [49.0, 51.0], [2.0, 1.0]],
    #             [[0.0, 0.0], [6.0, 7.0], [50.0, 50.0], [6.0, 6.0]],
    #             [[0.0, 0.0], [6.0, 7.0], [51.0, 49.0], [6.0, 7.0]],
    #             [[0.0, 0.0], [8.0, 7.0], [50.0, 50.0], [5.0, 6.0]],
    #             [[0.0, 0.0], [7.0, 6.0], [49.0, 51.0], [7.0, 6.0]],
    #             [[0.0, 0.0], [7.0, 6.0], [50.0, 50.0], [6.0, 6.0]],
    #             [[0.0, 0.0], [7.0, 7.0], [50.0, 50.0], [6.0, 6.0]],
    #             [[0.0, 0.0], [12.0, 12.0], [50.0, 50.0], [1.0, 1.0]],
    #             [[0.0, 0.0], [1.0, 12.0], [50.0, 50.0], [12.0, 1.0]],
    #             [[0.0, 0.0], [12.0, 1.0], [50.0, 50.0], [1.0, 12.0]],
    #             [[0.0, 0.0], [7.0, 6.0], [50.0, 50.0], [6.0, 7.0]],
    #             [[0.0, 0.0], [6.0, 7.0], [50.0, 50.0], [7.0, 6.0]],
    #             [[0.0, 0.0], [14.0, 1.0], [48.0, 52.0], [1.0, 10.0]],
    #         ],
    #     )
    #     # self.assertEqual(x, [[0.0, 0.0], [6.0, 6.0], [50.0, 50.0], [7.0, 6.0]])

    # def test_rps2(self):
    #     workflow = "TestCase3Workflow"
    #     toleranceWindow = 0
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCase3Workflow"
    #         + ".json"
    #     )
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [
    #         [0.0],
    #         [0.0],
    #         [0.0],
    #         [0.0],
    #     ]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     solver = rpsOffloadingSolver(
    #         workflow=workflow,
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [{"cores": 100, "mem_mb": 10000}]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     self.assertEqual(x, [[0.0], [100.0], [100.0], [100.0]])

    # def test_rps3(self):
    #     workflow = "TestCase3Workflow"
    #     toleranceWindow = 0
    #     jsonPath = (
    #         str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
    #         + "/log-parser/get-workflow-logs/data/"
    #         + "TestCase3Workflow"
    #         + ".json"
    #     )
    #     with open(jsonPath, "r") as json_file:
    #         workflow_json = json.load(json_file)
    #     workflow_json["lastDecision_default"] = [
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #         [0.0, 0.0],
    #     ]
    #     with open(jsonPath, "w") as json_file:
    #         json.dump(workflow_json, json_file)
    #     solver = rpsOffloadingSolver(
    #         workflow=workflow,
    #         mode=self.mode,
    #         decisionMode=None,
    #         toleranceWindow=toleranceWindow,
    #         rps=self.rps,
    #         testingFlag=True,
    #     )
    #     availResources = [
    #         {"cores": 10000, "mem_mb": 300000},
    #         {"cores": 10000, "mem_mb": 300000},
    #     ]
    #     alpha = 0
    #     x = solver.suggestBestOffloadingMultiVM(
    #         availResources=availResources, alpha=alpha, verbose=True
    #     )
    #     self.assertEqual(x, [[0.0, 0.0], [50.0, 50.0], [50.0, 50.0], [50.0, 50.0]])

    def test_rpsN(self):
        n_tests = 1
        n_funcs_list = [n for n in range(4, 41, 4)]
        n_hosts_list = [1] + [n for n in range(4, 21, 4)]
        repeats = 3
        # n_funcs_list = [50]
        # n_hosts_list = [25]
        # repeats = 1

        results = []
        print(n_hosts_list)
        print(n_funcs_list)
        for n_funcs in n_funcs_list:
            for n_hosts in n_hosts_list:
                n_funcs, n_hosts = int(n_funcs), int(n_hosts)
                print((n_funcs, n_hosts))
                tgen = TestCaseGenerator(n_funcs, n_hosts)
                tgen.build()
                workflow = "TestCaseNWorkflow"
                toleranceWindow = 0
                availResources = [{"cores": 10, "mem_mb": 300}]*n_hosts
                alpha = 0.1
                solver = rpsOffloadingSolver(
                    workflow=workflow,
                    mode=self.mode,
                    decisionMode=None,
                    toleranceWindow=toleranceWindow,
                    rps=self.rps,
                    testingFlag=True,
                )
                for k in range(repeats):
                    start = time.time()
                    x_gekko = solver.suggestBestOffloadingMultiVMGekko(
                        availResources=availResources, alpha=alpha, verbose=True
                    )
                    end = time.time()
                    time_gekko = end-start
                    print(f'GEKKO = {time_gekko} -> {x_gekko}')
                    
                    if x_gekko == 'NotFound':
                        cost_gekko = float('inf')
                    else:
                        cost_gekko = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x_gekko)
                    
                    print(f'COST GEKKO {cost_gekko}')

                    start = time.time()
                    solver = rpsOffloadingSolver(
                        workflow=workflow,
                        mode=self.mode,
                        decisionMode=None,
                        toleranceWindow=toleranceWindow,
                        rps=self.rps,
                        testingFlag=True,
                    )
                    x_julia = solver.suggestBestOffloadingMultiVM(
                        availResources=availResources, alpha=alpha, verbose=True
                    )
                    end = time.time()
                    time_julia = end-start
                    
                    if x_julia == 'NotFound':
                        cost_julia = float('inf')
                    else:
                        cost_julia = solver.calcLatencyCost(alpha, solver.offloadingCandidates, availResources, x_julia)
                    
                    print(f'Julia = {time_julia} -> {x_julia}')
                    print(f'COST JULIA {cost_julia}')

                    results.append({
                        "n_funcs": n_funcs,
                        "n_hosts": n_hosts,
                        "time_gekko": time_gekko,
                        "time_julia": time_julia,
                        "sol_gekko": x_gekko,
                        "cost_gekko": cost_gekko,
                        "sol_julia": x_julia,
                        "cost_julia": cost_julia
                    })

                    


                    #print(x)

                tgen.delete()
                print('-----------') 

        print(results)

        pd.DataFrame(results).to_csv('/home/pjavan/unfaasener/tests/Timing_df_Gekko.csv')

if __name__ == "__main__":
    unittest.main()

