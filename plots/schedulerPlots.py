import matplotlib.pyplot as plt
import pandas as pd
import copy
from pathlib import Path
import os
import sys
import numpy as np
import math
import json
import seaborn as sns


class getPlots:
    def __init__(self, workflow):
        self.workflow = workflow
        dfPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/generatedDataFrame.pkl"
        )
        self.dataframe = pd.read_pickle(dfPath)
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            self.workflow_json = json.load(json_file)
        self.exePlot()
        self.latencyPlot()
        self.costPlot()

    def getArrivalTime(self, startByReq, reqID):
        if reqID in startByReq.keys():
            return startByReq[reqID]
        else:
            return np.nan

    def exePlot(self):
        startByReq = self.getArrivalDict()
        plt.figure()
        Temps = copy.deepcopy(self.dataframe)
        Temps = Temps[["host", "reqID"]]
        Temps["arrivalDate"] = Temps.apply(
            lambda row: self.getArrivalTime(startByReq, row.reqID),
            axis=1,
        )
        Temps = Temps[Temps['arrivalDate'].notna()]
        Temps = Temps[["arrivalDate", "host"]]
        tempDict = (Temps.groupby(["arrivalDate", "host"])["host"].count()).to_dict()
        dataTemp = pd.Series(tempDict).rename_axis(['arrivalDate', 'host']).reset_index(name='counts')
        print(dataTemp)
        plt.figure()
        g = sns.catplot(x="arrivalDate", hue="host", y="counts",data=dataTemp)
        plt.show()
        plt.savefig(self.workflow + "/invocations.png")

    def latencyPlot(self):
        terminals = self.findTerminals()
        plt.figure()
        startByReq = self.getArrivalDict()
        endTemp = copy.deepcopy(self.dataframe)
        endTemp = (endTemp[(endTemp.function.isin(terminals))])[["reqID", "finish"]]
        endTemp["finish"] = pd.to_datetime(endTemp["finish"], utc=True)
        endTempGroup = endTemp.groupby(["reqID"])
        endDF = endTempGroup.agg(Maximum_Date=("finish", np.max))
        endDF = endDF.to_dict()["Maximum_Date"]
        startByReqSet = set(startByReq)
        endDFSet = set(endDF)
        finalDict = {}
        for keyy in startByReqSet.intersection(endDFSet):
            duration = ((endDF[keyy] - startByReq[keyy]).total_seconds()) * 1000
            finalDict[startByReq[keyy]] = duration
        plt.figure()
        arrival_time, duration = zip(*sorted(finalDict.items()))
        plt.plot(arrival_time, duration)
        plt.xlabel("Invocation Arrival Time")
        plt.ylabel("End-to-end Latency (milliseconds)")
        plt.show()
        plt.savefig(self.workflow + "/latency.png")

    def costPlot(self):
        startByReq = self.getArrivalDict()
        memories = self.workflow_json["memory"]
        workflowFunctions = self.workflow_json["workflowFunctions"]
        Temps = copy.deepcopy(self.dataframe)
        Temps = Temps[["host", "function", "reqID", "duration"]]
        Temps["cost"] = Temps.apply(
            lambda row: self.cost_estimator(
                row.duration, memories[workflowFunctions.index(row.function)], row.host
            ),
            axis=1,
        )
        costlDF = Temps[["cost", "reqID"]]
        costlDF = (costlDF.groupby("reqID")["cost"].sum()).to_dict()
        startByReqSet = set(startByReq)
        costlDFSet = set(costlDF)
        finalDict = {}
        for keyy in startByReqSet.intersection(costlDFSet):
            finalDict[startByReq[keyy]] = costlDF[keyy]
        plt.figure()
        arrival_time, cost = zip(*sorted(finalDict.items()))
        plt.plot(arrival_time, cost)
        plt.xlabel("Invocation Arrival Time")
        plt.ylabel("Accumulated Cost")
        plt.show()
        plt.savefig(self.workflow + "/cost.png")

    def getArrivalDict(self):
        Temps = copy.deepcopy(self.dataframe)
        Temps = Temps[["start", "function", "reqID"]]
        Temps["start"] = pd.to_datetime(Temps["start"], utc=True)
        startByReq = Temps.loc[(Temps["function"] == self.workflow_json["initFunc"])]
        startByReq = startByReq.set_index("reqID").to_dict()["start"]
        return startByReq

    def cost_estimator(self, ET, GB, host):
        if host != "s":
            return 0
        else:
            free_tier_invocations = 0
            free_tier_GB = 0
            free_tier_GHz = 0
            unit_price_invocation = 0.0000004
            unit_price_GB = 0.0000025
            unit_price_GHz = 0.0000100
            if GB == 0.125:
                Ghz = 0.2
            elif GB == 0.25:
                Ghz = 0.4
            elif GB == 0.5:
                Ghz = 0.8
            elif GB == 1:
                Ghz = 1.4
            elif GB == 2:
                Ghz = 2.4
            elif GB == 4:
                Ghz = 4.8
            elif GB == 8:
                Ghz = 4.8
            costInvoke = unit_price_invocation
            costGB = ((math.ceil(ET / 100)) * 0.1 * GB) * unit_price_GB
            costGhz = ((math.ceil(ET / 100)) * 0.1 * Ghz) * unit_price_GHz
            cost = costInvoke + costGB + costGhz
            return cost

    def findTerminals(self):
        terminals = []
        workflowFunctions = self.workflow_json["workflowFunctions"]
        workflowSuccessors = self.workflow_json["successors"]
        for each in workflowSuccessors:
            if len(each) == 0:
                terminals.append(workflowFunctions[workflowSuccessors.index(each)])
        return terminals


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = sys.argv[1]
    x = getPlots(workflow)
