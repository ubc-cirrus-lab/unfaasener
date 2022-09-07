import matplotlib.pyplot as plt
import pandas as pd
import configparser
import copy
from pathlib import Path
import datetime
import os
import sys
import numpy as np
import math
import json
import seaborn as sns
from matplotlib.pyplot import figure
from sklearn.preprocessing import MinMaxScaler
import matplotlib

BIGGER_SIZE = 35
matplotlib.rc("font", size=BIGGER_SIZE)
matplotlib.rc("axes", titlesize=BIGGER_SIZE)


class getPlots:
    def __init__(self, workflow):
        path = str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/dateTest.ini"
        config = configparser.ConfigParser()
        config.read(path)
        dateConfig = config["settings"]
        self.startTestDate = dateConfig["date"]
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
        Temps = copy.deepcopy(self.dataframe)
        Temps = Temps[["host", "start", "finish"]]
        Temps["start"] = pd.to_datetime(Temps["start"], utc=True)
        Temps["finish"] = pd.to_datetime(Temps["finish"], utc=True)
        cols_to_norm = ["start", "finish"]
        startTestDate = datetime.datetime.strptime(
            (self.startTestDate), "%Y-%m-%d %H:%M:%S.%f"
        )
        dictStartT = {"startTest": ([startTestDate] * 10)}
        dfStartT = pd.DataFrame(dictStartT)
        dfStartT["startTest"] = pd.to_datetime(dfStartT["startTest"], utc=True)
        minDate = dfStartT["startTest"].min()
        minDateData = (
            (Temps.loc[(Temps["start"] >= minDate) & (Temps["host"] == "s")])["start"]
        ).min()
        print("min:::", minDate)
        print("min Data:::", minDateData)
        maxDateStart = Temps["start"].max()
        maxDateFinish = Temps["finish"].max()
        maxDate = max(maxDateStart, maxDateFinish)
        Temps2 = copy.deepcopy(self.dataframe)
        Temps2 = Temps2[["host", "start", "finish"]]
        Temps2 = Temps2.loc[Temps2["host"] == "s"]
        Temps2["start"] = pd.to_datetime(Temps2["start"], utc=True)
        Temps2["finish"] = pd.to_datetime(Temps2["finish"], utc=True)
        Temps2["dummy"] = 1
        Temps3 = copy.deepcopy(self.dataframe)
        Temps3 = Temps3[["host", "start", "finish"]]
        Temps3 = Temps3.loc[Temps3["host"] == "vm0"]
        Temps3["start"] = pd.to_datetime(Temps3["start"], utc=True)
        Temps3["finish"] = pd.to_datetime(Temps3["finish"], utc=True)
        Temps3["dummy"] = 1
        date_series = pd.date_range(
            (minDateData - datetime.timedelta(0, 1)),
            (maxDate + datetime.timedelta(0, 1)),
            freq="1S",
        )
        datedf = pd.DataFrame(dict(date=date_series, dummy=1))
        crossJoin = datedf.merge(Temps2, on="dummy")
        condJoin = crossJoin[
            (crossJoin.start <= crossJoin.date) & (crossJoin.date <= crossJoin.finish)
        ]
        joinGrp = condJoin.groupby(["date"])
        final = (
            pd.DataFrame(dict(serverless=joinGrp.size()), index=date_series)
            .fillna(0)
            .reset_index()
        )
        crossJoin2 = datedf.merge(Temps3, on="dummy")
        condJoin2 = crossJoin2[
            (crossJoin2.start <= crossJoin2.date)
            & (crossJoin2.date <= crossJoin2.finish)
        ]
        joinGrp2 = condJoin2.groupby(["date"])
        final2 = (
            pd.DataFrame(dict(vm0=joinGrp2.size()), index=date_series)
            .fillna(0)
            .reset_index()
        )
        finalFrame = final.merge(final2, on="index")
        finalFrame["vm0"] = finalFrame.apply(
            lambda row: self.getVmCount(row.vm0, row.serverless),
            axis=1,
        )
        finalFrame["index"] = finalFrame["index"].apply(
            lambda x: (x - finalFrame["index"].min()).total_seconds()
        )
        plt.figure(figsize=(40, 10), linewidth=3)
        # finalFrame.set_index("index")[["vm0", "serverless"]].plot(
        #     figsize=(40, 10), linewidth=3
        # )
        plt.plot([],[],color='#d2e69c', label='serverless', linewidth=6)
        plt.plot([],[],color='#B5179E', label='vm0', linewidth=6)
        plt.stackplot(finalFrame["index"], finalFrame["serverless"], finalFrame["vm0"],
              colors =['#d2e69c', '#B5179E'])
        plt.xlabel("Time(Seconds)")
        plt.ylabel("Concurrency")
        plt.legend()
        plt.show()
        plt.savefig(self.workflow + "/invocations.png")

    def getVmCount(self, count_vm0, count_s):
        total = count_vm0 + count_s
        # if total == count_s:
        #     return np.nan
        # else:
        return total

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
        minStart = min(list(startByReq.values()))
        endDFSet = set(endDF)
        finalDict = {}
        for keyy in startByReqSet.intersection(endDFSet):
            duration = ((endDF[keyy] - startByReq[keyy]).total_seconds()) * 1000
            finalDict[(startByReq[keyy] - minStart).total_seconds()] = duration
        plt.figure(figsize=(12, 10), dpi=80)
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
        plt.figure(figsize=(12, 10), dpi=80)
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
