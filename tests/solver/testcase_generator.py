import os
import json
from pathlib import Path
import pandas as pd
import random


class TestCaseGenerator:
    def __init__(self, n_funcs, n_hosts):
        self.n_funcs = n_funcs
        self.n_hosts = n_hosts

    def build(self):
        log_data = []

        for i in range(self.n_funcs):
            for id in range(10):
                log_data.append(
                    {
                        "function": f"Func_{i}",
                        "reqID": id,
                        "start": "",
                        "finish": "",
                        "mergingPoint": "",
                        "host": "s",
                        "duration": 100,
                    }
                )

        for j in range(self.n_hosts):
            for i in range(self.n_funcs):
                for id in range(10):
                    log_data.append(
                        {
                            "function": f"Func_{i}",
                            "reqID": id,
                            "start": "",
                            "finish": "",
                            "mergingPoint": "",
                            "host": f"vm{j}",
                            "duration": 100,
                        }
                    )

        df = pd.DataFrame(log_data)
        df.to_csv(
            "../log-parser/get-workflow-logs/data/TestCaseNWorkflow/generatedDataFrame.csv"
        )
        # df.to_csv('/home/pjavan/unfaasener/tests/logCollector/TestCaseNWorkflow/generatedDataFrame.csv')

        costs_dict = {}
        pubSub_dict = {}
        slack_data = {}

        successors = []
        predecessors = []
        workflowFunctions = []
        last_dec = []

        for i in range(self.n_funcs):
            func_name = f"Func_{i}"
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

            costs_dict[func_name] = {
                "best-case": 4.6399999999999997e-07,
                "worst-case": 4.6399999999999997e-07,
                "default": 4.6399999999999997e-07,
            }

            pubSub_dict[func_name] = 100000000000
            slack_data[func_name] = {
                "best-case": 0.0,
                "worst-case": 0.0,
                "default": 0.0,
            }
            if i < self.n_funcs - 1:
                slack_data[f"Func_{i}-Func_{i+1}"] = {
                    "best-case": 0.0,
                    "worst-case": 0.0,
                    "default": 0.0,
                }
                successors.append([f"Func_{i+1}"])
            else:
                successors.append([])

            if i > 0:
                predecessors.append([f"Func_{i-1}"])
            else:
                predecessors.append([])

            if random.randint(1, 10) > 5:
                last_dec.append([1.0] * self.n_hosts)
            else:
                last_dec.append([0.0] * self.n_hosts)

        workflow_dict = {
            "workflow": "TestCaseNWorkflow",
            "workflowFunctions": workflowFunctions,
            "initFunc": "Func_0",
            "successors": successors,
            "predecessors": predecessors,
            "memory": [1 / self.n_funcs] * self.n_funcs,
            "lastDecision_default": last_dec,
            "lastDecision_best-case": last_dec,
            "lastDecision_worst-case": last_dec,
            "topics": [""] + ["dag-Profanity"] * (self.n_funcs - 1),
        }

        jsonPath = (
            "../log-parser/get-workflow-logs/data/" + "TestCaseNWorkflow" + ".json"
        )
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_dict, json_file)

        base_dir = "./data/TestCaseNWorkflow"

        with open(f"{base_dir}/Costs.json", "w") as outfile:
            json.dump(costs_dict, outfile)

        with open(f"{base_dir}/pubSubSize.json", "w") as outfile:
            json.dump(pubSub_dict, outfile)

        with open(f"{base_dir}/slackData.json", "w") as outfile:
            json.dump(slack_data, outfile)

        with open(f"{base_dir}/slackDurations.json", "w") as outfile:
            json.dump(slack_data, outfile)

    def delete(self):
        base_dir = "./data/TestCaseNWorkflow"
        os.system(
            "rm ../log-parser/get-workflow-logs/data/TestCaseNWorkflow/generatedDataFrame.csv"
        )
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


if __name__ == "__main__":
    n_funcs, n_hosts = 30, 10
    tgen = TestCaseGenerator(n_funcs, n_hosts)
    tgen.build()
