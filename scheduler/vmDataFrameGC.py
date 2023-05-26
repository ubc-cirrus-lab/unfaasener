import json
import os
import pandas as pd
from pathlib import Path

pd.options.mode.chained_assignment = None
import configparser


class VMgarbageCollector:
    def __init__(self, workflow):
        self.workflow = workflow
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + ".json"
        )
        self.vmcachePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/execution-agent/data/cachedVMData.csv"
        )
        if os.path.isfile(self.vmcachePath):
            self.dataframe = pd.read_csv(self.vmcachePath)
        else:
            return

        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.initFunc = workflow_json["initFunc"]
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.predecessors = workflow_json["predecessors"]
        self.successors = workflow_json["successors"]
        self.recordNum = 0
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.windowSize = int(self.rankerConfig["windowSize"])
        self.selectRecords()

    def selectRecords(self):
        self.dataframe["start"] = pd.to_datetime(self.dataframe["start"])
        self.dataframe.sort_values(by=["start"], ascending=False, inplace=True)
        g = self.dataframe.groupby(self.dataframe["reqID"], sort=False)
        self.dataframe = pd.concat(
            islice(map(itemgetter(1), g), max(0, g.ngroups - self.windowSize), None)
        )
        self.dataframe.to_csv(self.vmcachePath)


if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = "TestCaseWorkflow"
    x = garbageCollector(workflow)
    # x.getExecutionTime("vm0")
    # print(x.getFuncExecutionTime("D", "vm0", "worst-case"))
