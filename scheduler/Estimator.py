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
import math
from monitoring import monitoring
from pathlib import Path
import rankerConfig
import statistics


class Estimator:
    def __init__(self, workflow):
        self.workflow = workflow
        jsonPath = (
            str(Path(os.getcwd()).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + ".json"
        )
        if os.path.isfile(
            str(Path(os.getcwd()).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/generatedDataFrame.pkl"
        ):
            dataframePath = (
                str(Path(os.getcwd()).resolve().parents[0])
                + "/log_parser/get_workflow_logs/data/"
                + self.workflow
                + "/generatedDataFrame.pkl"
            )
            self.dataframe = pd.read_pickle(dataframePath)
        elif os.path.isfile(
            str(Path(os.getcwd()).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/generatedDataFrame.csv"
        ):
            dataframePath = (
                str(Path(os.getcwd()).resolve().parents[0])
                + "/log_parser/get_workflow_logs/data/"
                + self.workflow
                + "/generatedDataFrame.csv"
            )
            self.dataframe = pd.read_csv(dataframePath)
        else:
            print("Dataframe not found!")
            self.dataframe = None
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.initFunc = workflow_json["initFunc"]
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.predecessors = workflow_json["predecessors"]
        self.successors = workflow_json["successors"]
        self.topics = workflow_json["topics"]
        self.windowSize = 50
        self.memories = workflow_json["memory"]

    def prev_cost(self):

        with open(
            os.getcwd() + "/data/" + self.workflow + "-prevCost.json", "r"
        ) as json_file:
            workflow_json = json.load(json_file)
        return workflow_json

    def cost_estimator(self, NI, ET, GB):
        free_tier_invocations = 2000000
        free_tier_GB = 400000
        free_tier_GHz = 200000
        prev_Json = self.prev_cost()
        if prev_Json["NI"] > free_tier_invocations:
            free_tier_invocations = 0
        else:
            free_tier_invocations = free_tier_invocations - prev_Json["NI"]
        if prev_Json["GB-Sec"] > free_tier_GB:
            free_tier_GB = 0
        else:
            free_tier_GB = free_tier_GB - prev_Json["GB-Sec"]
        if prev_Json["GHz-Sec"] > free_tier_GHz:
            free_tier_GHz = 0
        else:
            free_tier_GHz = free_tier_GHz - prev_Json["GHz-Sec"]
        unit_price_invocation = 0.0000004
        unit_price_GB = 0.0000025
        unit_price_GHz = 0.0000100
        if GB == 0.128:
            Ghz = 0.2
        elif GB == 0.256:
            Ghz = 0.4
        elif GB == 0.512:
            Ghz = 0.8
        elif GB == 1:
            Ghz = 1.4
        elif GB == 2:
            Ghz = 2.4
        elif GB == 4:
            Ghz = 4.8
        elif GB == 8:
            Ghz = 4.8
        costInvoke = max(0, (NI - free_tier_invocations) * unit_price_invocation)
        costGB = max(
            0,
            (((NI * (math.ceil(ET / 100)) * 0.1 * GB) - free_tier_GB) * unit_price_GB),
        )
        costGhz = max(
            0,
            (
                ((NI * (math.ceil(ET / 100)) * 0.1 * Ghz) - free_tier_GHz)
                * unit_price_GHz
            ),
        )
        cost = costInvoke + costGB + costGhz
        return cost

    def getUpperBound(self, array):
        n = len(array)
        if n <= 30:
            upperBound = 90
            # upperBound =  np.percentile(array, 75)
        else:
            sortedArray = np.sort(array)
            z = 1.96
            index = int(np.ceil(1 + ((n + (z * (np.sqrt(n)))) / 2)))
            upperBound = sortedArray[index]
        return upperBound

    def getMedian(self, array):
        median = statistics.median(array)
        return median

    def getLowerBound(self, array):
        n = len(array)
        if n <= 30:
            lowerBound = 90
            # lowerBound =  np.percentile(array, 25)
        else:
            sortedArray = np.sort(array)
            z = 1.96
            index = int(np.floor((n - (z * (np.sqrt(n)))) / 2))
            lowerBound = sortedArray[index]
        return lowerBound

    def getExecutionTime(self, host):
        exeTimes = {}
        decisionModes = rankerConfig.decisionMode
        for func in self.workflowFunctions:
            exeTimes[func] = {}
        for mode in decisionModes:
            for func in self.workflowFunctions:
                durations = []
                selectedInits = self.dataframe.loc[
                    (self.dataframe["function"] == func)
                    & (self.dataframe["host"] == host)
                ]
                selectedInits["start"] = pd.to_datetime(selectedInits["start"])
                selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
                if (selectedInits.shape[0]) >= self.windowSize:
                    selectedInits = selectedInits.head(self.windowSize)
                for i, record in selectedInits.iterrows():
                    durations.append(record["duration"])
                if mode == "best-case":
                    if host == "s":
                        exeTimes[func][mode] = self.getUpperBound(durations)
                    else:
                        exeTimes[func][mode] = self.getLowerBound(durations)

                elif mode == "worst-case":
                    if host == "s":
                        exeTimes[func][mode] = self.getLowerBound(durations)
                    else:
                        exeTimes[func][mode] = self.getUpperBound(durations)
                elif mode == "default":
                    exeTimes[func][mode] = self.getMedian(durations)
        with open(
            (
                os.getcwd()
                + "/data/"
                + str(self.workflow)
                + "/"
                + host
                + ", exeTime.json"
            ),
            "w",
        ) as outfile:
            json.dump(exeTimes, outfile)

    def cost_estimator_pubsub(self, bytes):
        free_tier_Bytes = 1024 * 1024 * 1024
        prev_Json = self.prev_cost()
        unit_price_TiB = 40

        if prev_Json["Bytes"] > free_tier_Bytes:
            free_tier_Bytes = 0
        else:
            free_tier_Bytes = free_tier_Bytes - prev_Json["Bytes"]
        calculatedbytes = max(
            0, ((max(1024, bytes) - free_tier_Bytes) / (1024 * 1024 * 1024 * 1024))
        )
        costB = calculatedbytes * unit_price_TiB
        return costB

    def getPubsubDF(self):
        monitoringObj = monitoring()
        topicMsgSize = pd.read_pickle(os.getcwd() + "/data/" + "topicMsgSize.pkl")
        return topicMsgSize

    # func: function a message is published to (subscriber)
    def getPubSubCost(self, func):
        psSize = self.getPubSubSize(func)
        cost = self.cost_estimator_pubsub(psSize)
        return cost

    # func: function a message is published to (subscriber)
    def getPubSubSize(self, func):
        pubsubsizeDF = self.getPubsubDF()
        selectedtopic = self.topics[self.workflowFunctions.index(func)]
        psSize = pubsubsizeDF.loc[
            pubsubsizeDF["Topic"] == selectedtopic, "PubsubMsgSize"
        ].item()
        return psSize

    def getPubSubMessageSize(self):
        pubSubSize = {}
        pubsubsizeDF = self.getPubsubDF()
        for func in self.workflowFunctions:
            if func != self.initFunc:
                selectedtopic = self.topics[self.workflowFunctions.index(func)]
                psSize = pubsubsizeDF.loc[
                    pubsubsizeDF["Topic"] == selectedtopic, "PubsubMsgSize"
                ].item()
                pubSubSize[func] = psSize
        with open(
            (os.getcwd() + "/data/" + str(self.workflow) + "/" + "pubSubSize.json"), "w"
        ) as outfile:
            json.dump(pubSubSize, outfile)

    def getComCost(self, msgSize):
        cost = self.cost_estimator_pubsub(msgSize)
        return cost

    def getFuncExecutionTime(self, func, host, mode):
        exeTime = 0
        durations = []
        selectedInits = self.dataframe.loc[
            (self.dataframe["function"] == func) & (self.dataframe["host"] == host)
        ]
        selectedInits["start"] = pd.to_datetime(selectedInits["start"])
        selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
        if (selectedInits.shape[0]) >= self.windowSize:
            selectedInits = selectedInits.head(self.windowSize)
        for i, record in selectedInits.iterrows():
            durations.append(record["duration"])
        if mode == "best-case":
            if host == "s":
                exeTime = self.getUpperBound(durations)
            else:
                exeTime = self.getLowerBound(durations)

        elif mode == "worst-case":
            if host == "s":
                exeTime = self.getLowerBound(durations)
            else:
                exeTime = self.getUpperBound(durations)
        elif mode == "default":
            exeTime = self.getMedian(durations)
        return exeTime

    def getCost(self):
        costs = {}
        decisionModes = rankerConfig.decisionMode
        for func in self.workflowFunctions:
            costs[func] = {}
        for mode in decisionModes:
            for func in self.workflowFunctions:
                GB = self.memories[self.workflowFunctions.index(func)]
                durations = []
                selectedInits = self.dataframe.loc[
                    (self.dataframe["function"] == func)
                    & (self.dataframe["host"] == "s")
                ]
                selectedInits["start"] = pd.to_datetime(selectedInits["start"])
                selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
                if (selectedInits.shape[0]) >= self.windowSize:
                    selectedInits = selectedInits.head(self.windowSize)
                for i, record in selectedInits.iterrows():
                    durations.append(record["duration"])
                if mode == "best-case":
                    et = self.getUpperBound(durations)
                    costs[func][mode] = self.cost_estimator(1, et, GB)

                elif mode == "worst-case":
                    et = self.getLowerBound(durations)
                    costs[func][mode] = self.cost_estimator(1, et, GB)
                elif mode == "default":
                    et = self.getMedian(durations)
                    costs[func][mode] = self.cost_estimator(1, et, GB)
        with open(
            (os.getcwd() + "/data/" + str(self.workflow) + "/" + "Costs.json"), "w"
        ) as outfile:
            json.dump(costs, outfile)

    def getFuncCost(self, mode, func):

        GB = self.memories[self.workflowFunctions.index(func)]
        durations = []
        selectedInits = self.dataframe.loc[
            (self.dataframe["function"] == func) & (self.dataframe["host"] == "s")
        ]
        selectedInits["start"] = pd.to_datetime(selectedInits["start"])
        selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
        if (selectedInits.shape[0]) >= self.windowSize:
            selectedInits = selectedInits.head(self.windowSize)
        for i, record in selectedInits.iterrows():
            durations.append(record["duration"])
        if mode == "best-case":
            et = self.getUpperBound(durations)
            cost = self.cost_estimator(1, et, GB)

        elif mode == "worst-case":
            et = self.getLowerBound(durations)
            cost = self.cost_estimator(1, et, GB)
        elif mode == "default":
            et = self.getMedian(durations)
            cost = self.cost_estimator(1, et, GB)
        return cost


if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = "TestCaseWorkflow"
    x = Estimator(workflow)
    x.getCost()
    x.getExecutionTime("s")
    x.getPubSubMessageSize()
    # x.getExecutionTime("vm0")
    # print(x.getFuncExecutionTime("D", "vm0", "worst-case"))
