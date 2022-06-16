from re import S
import subprocess
import json
import shlex
import datetime
from sys import getsizeof
import time
import os
import pandas as pd
import numpy as np
import seaborn as sns
import math
import networkx as nx
from monitoring import monitoring
from criticalpath import Node
from pathlib import Path
import rankerConfig
import statistics


class Estimator:
    def __init__(self, workflow):
        self.workflow = workflow
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + ".json"
        )
        dataframePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/generatedDataFrame.pkl"
        )
        self.dataframe = pd.read_pickle(dataframePath)

        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.initFunc = workflow_json["initFunc"]
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.predecessors = workflow_json["predecessors"]
        self.successors = workflow_json["successors"]
        self.recordNum = 0
        self.windowSize = 50
        self.slackData = {}
        self.dependencies = []
        self.recordNum = len(self.workflowFunctions)
        for func in self.workflowFunctions:
            if len(self.predecessors[self.workflowFunctions.index(func)]) > 1:
                self.recordNum += (
                    len(self.predecessors[self.workflowFunctions.index(func)])
                ) - 1
        self.memories = workflow_json["memory"]
        self.selectedIDs = self.selectRecords()
        self.getLastObservations()
        # self.dataframe.to_pickle(dataframePath)

    def selectRecords(self):
        selectedInits = self.dataframe.loc[self.dataframe["function"] == self.initFunc]
        selectedInits["start"] = pd.to_datetime(selectedInits["start"])
        selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
        selectedRecords = []
        for i, record in selectedInits.iterrows():
            selectedReq = self.dataframe.loc[
                (self.dataframe["reqID"] == record["reqID"])
                & (self.dataframe["host"] == "s")
            ]
            if selectedReq.shape[0] == self.recordNum:
                selectedRecords.append(record["reqID"])
        if len(selectedRecords) >= self.windowSize:
            selectedRecords = selectedRecords[: self.windowSize]
        self.finalRecodreqID = selectedRecords[-1]
        return selectedRecords

    def getLastObservations(self):
        for func in self.workflowFunctions:
            selectedReq = self.dataframe.loc[
                (self.dataframe["reqID"] == self.finalRecodreqID)
                & (self.dataframe["function"] == func)
            ]
            selectedReqForFunc = selectedReq.iloc[0]["start"]
            startDate = selectedReqForFunc
            # startDate = datetime.date((selectedReqForFunc["start"])
            self.dataframe["start"] = pd.to_datetime(
                self.dataframe["start"], format="%Y-%m-%d %H:%M:%S.%f"
            )
            # self.dataframe
            # selected = self.dataframe.loc[
            #     (self.dataframe["function"] == func)
            #     & (self.dataframe["host"] == "s")
            #     & ((self.dataframe["start"]) < startDate)
            # ]
            selected = self.dataframe.drop(
                self.dataframe[
                    (self.dataframe["function"] == func)
                    & (self.dataframe["host"] == "s")
                    & ((self.dataframe["start"]) < startDate)
                ].index,
                inplace=True,
            )
            print("func:::", func)
            print(selected)


if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = "TestCaseWorkflow"
    x = Estimator(workflow)
    # x.getExecutionTime("vm0")
    # print(x.getFuncExecutionTime("D", "vm0", "worst-case"))
