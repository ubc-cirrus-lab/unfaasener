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
import matplotlib
import logging

logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/plots.log",
    level=logging.INFO,
)

BIGGER_SIZE = 35
matplotlib.rc("font", size=BIGGER_SIZE)
matplotlib.rc("axes", titlesize=BIGGER_SIZE)


class getPlots:
    def __init__(self, workflow, rps, mode):
        self.currentRead = 0
        self.currentWrite = 0
        self.currentDelete = 0
        self.dataDict = {}
        self.dataDict["cost"] = []
        self.dataDict["rps"] = []
        self.dataDict["mean_latency"] = []
        self.dataDict["tail_latency"] = []
        self.dataDict["mode"] = []
        self.rps = rps
        self.dataDict["rps"].append(self.rps)
        self.dataDict["mode"].append(mode)
        path = str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/dateTest.ini"
        config = configparser.ConfigParser()
        config.read(path)
        dateConfig = config["settings"]
        self.startTestDate = dateConfig["date"]
        self.workflow = workflow
        dfDir = Path(str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/")
        dfFilesNames = [file.name for file in dfDir.iterdir() if ((file.name.startswith('generatedDataFrame')) and (file.name.endswith('.pkl')))]  
        dfFilesNames = [a.replace(".pkl", "") for a in dfFilesNames]
        versions = [int((a.split(","))[1]) for a in dfFilesNames]
        lastVersion = max(versions)
        dfPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/generatedDataFrame,"+str(lastVersion)+".csv"
        )
        dateDFPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + self.workflow
            + "/dateDate.csv"
        )
        self.dateDF = pd.read_csv(dateDFPath)
        self.dataframe = pd.read_csv(dfPath)
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
        totalCost = self.costPlot()
        print("Total Cost = " + str(totalCost))
        loggingTxt = "Total Cost = " + str(totalCost)
        self.dataDict["cost"].append(totalCost)
        logging.info(loggingTxt)
        self.saveRes()


    def saveRes(self):
        if os.path.isfile(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + "statsDataFrame.csv"
        ):
            prevDataframe = pd.read_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data"
                + "/statsDataFrame.csv"
            )
            newDataAdded = pd.DataFrame.from_dict(self.dataDict)
            newDataFrame = (
                pd.concat([prevDataframe, newDataAdded]).drop_duplicates().reset_index(drop=True)
            )
            newDataFrame.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + "statsDataFrame.csv"
            )

        else:
            newDataAdded = pd.DataFrame.from_dict(self.dataDict)
            newDataAdded.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + "statsDataFrame.csv"
            )

    def getArrivalTime(self, startByReq, reqID):
        if reqID in startByReq.keys():
            return startByReq[reqID]
        else:
            return np.nan

    def exePlot(self):
        self.dateDF["effected"] = pd.to_datetime(self.dateDF["effected"], utc=True)
        self.dateDF["triggered"] = pd.to_datetime(self.dateDF["triggered"], utc=True)
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
        minDateData = ((Temps.loc[(Temps["start"] >= minDate)])["start"]).min()

        print("min:::", minDate)
        print("min Data:::", minDateData)
        maxDateStart = Temps["start"].max()
        maxDateFinish = Temps["finish"].max()
        maxDate = max(maxDateStart, maxDateFinish)
        print(maxDate)
        dateDFChanged = self.dateDF[
            (self.dateDF.triggered >= minDateData)
            & (self.dateDF.triggered <= maxDate)
            & (self.dateDF.effected >= minDateData)
            & (self.dateDF.effected <= maxDate)
        ]
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
            (minDate),
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
        # finalFrame["vm0"] = finalFrame.apply(
        #     lambda row: self.getVmCount(row.vm0, row.serverless),
        #     axis=1,
        # )
        dateDFChanged["triggered"] = dateDFChanged["triggered"].apply(
            lambda x: (x - finalFrame["index"].min()).total_seconds()
        )
        dateDFChanged["effected"] = dateDFChanged["effected"].apply(
            lambda x: (x - finalFrame["index"].min()).total_seconds()
        )
        print("MIN:::", finalFrame["index"].min())
        print("MAX:::", finalFrame["index"].max())
        finalFrame["index"] = finalFrame["index"].apply(
            lambda x: (x - finalFrame["index"].min()).total_seconds()
        )
        triggered = dateDFChanged["triggered"]
        effected = dateDFChanged["effected"]
        plt.figure(figsize=(50, 10), linewidth=3)
        plt.plot([], [], color="#d2e69c", label="serverless", linewidth=6)
        plt.plot([], [], color="#B5179E", label="vm0", linewidth=6)
        plt.stackplot(
            finalFrame["index"],
            finalFrame["serverless"],
            finalFrame["vm0"],
            colors=["#d2e69c", "#B5179E"],
        )

        plt.vlines(
            x=triggered,
            ymin=0,
            ymax=max(finalFrame["serverless"] + finalFrame["vm0"]),
            color="salmon",
            label="scheduler-triggered",
            ls="--",
            lw=5,
        )
        plt.vlines(
            x=effected,
            ymin=0,
            ymax=max(finalFrame["serverless"] + finalFrame["vm0"]),
            color="teal",
            label="scheduler-effected",
            lw=5,
        )
        plt.xlabel("Time(Seconds)")
        plt.ylabel("Concurrency")
        plt.legend()
        plt.show()
        plt.savefig(self.workflow + "/invocations.png")

    def getVmCount(self, count_vm0, count_s):
        total = count_vm0 + count_s
        return total

    def latencyPlot(self):

        terminals = self.findTerminals()
        plt.figure()
        ttTemp = copy.deepcopy(self.dataframe)
        # ttTemp = ttTemp[ttTemp["function"] == "Text2SpeechCensoringWorkflow_MergedFunction"]
        df2 = ttTemp.groupby(["reqID"])["reqID"].count().to_dict()
        startTestDate = datetime.datetime.strptime(
            (self.startTestDate), "%Y-%m-%d %H:%M:%S.%f"
        )
        dictStartT = {"startTest": ([startTestDate] * 10)}
        dfStartT = pd.DataFrame(dictStartT)
        dfStartT["startTest"] = pd.to_datetime(dfStartT["startTest"], utc=True)
        minDate = dfStartT["startTest"].min()
        ttTemp["start"] = pd.to_datetime(ttTemp["start"], utc=True)
        testing = ttTemp[ttTemp["start"] > minDate]
        print("num:", len(testing))
        print("startTest::", minDate)
        print("MAx::Time::", testing["start"].max())
        print("MAx::Time::Finsih::", testing["finish"].max())
        print("diff reqs:", len(testing["reqID"].unique()))
        df2 = testing.groupby(["reqID"])["reqID"].count().to_dict()
        # print(df2)
        for x in df2:
            if df2[x] != 8:
                print(x, "::", df2[x])
        startByReq = self.getArrivalDict()
        endTemp = copy.deepcopy(self.dataframe)
        endTemp = (endTemp[(endTemp.function.isin(terminals))])[["reqID", "finish", "start"]]
        endTemp["finish"] = pd.to_datetime(endTemp["finish"], utc=True)
        endTemp["start"] = pd.to_datetime(endTemp["start"], utc=True)
        endTemp = endTemp[endTemp["start"] > minDate]
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
        # print("ArrivalTimes:", arrival_time)
        print("Durations", duration)
        median = np.percentile(duration, 50)
        meanRes = np.mean(duration)
        tail = np.percentile(duration, 75)
        nintyFive = np.percentile(duration, 95)
        twentyFive = np.percentile(duration, 25)
        print("median: ", median)
        print("95 percentile:", nintyFive)
        print("75 percentile:", tail)
        print("25 percentile:", twentyFive)
        print("mean: ", meanRes)
        self.dataDict["mean_latency"].append(meanRes)
        self.dataDict["tail_latency"].append(nintyFive)
        plt.xlabel("Invocation Arrival Time")
        plt.ylabel("End-to-end Latency (milliseconds)")
        plt.show()
        plt.savefig(self.workflow + "/latency.png")

    def costPlot(self):
        startByReq = self.getArrivalDict()
        memories = self.workflow_json["memory"]
        workflowFunctions = self.workflow_json["workflowFunctions"]
        Temps = copy.deepcopy(self.dataframe)
        Temps = Temps[["host", "function", "reqID", "duration", "mergingPoint", "start"]]
        startTestDate = datetime.datetime.strptime(
            (self.startTestDate), "%Y-%m-%d %H:%M:%S.%f"
        )
        dictStartT = {"startTest": ([startTestDate] * 10)}
        dfStartT = pd.DataFrame(dictStartT)
        dfStartT["startTest"] = pd.to_datetime(dfStartT["startTest"], utc=True)
        minDate = dfStartT["startTest"].min()
        # ttTemp["start"] = pd.to_datetime(ttTemp["start"], utc=True)
        # testing = ttTemp[ttTemp["start"] > minDate]
        # Temps = Temps[["start", "function", "reqID"]]
        Temps["start"] = pd.to_datetime(Temps["start"], utc=True)
        Temps = Temps[Temps["start"] > minDate]
        Temps["cost"] = Temps.apply(
            lambda row: self.cost_estimator(
                row.duration, memories[workflowFunctions.index(row.function)], row.host
            ),
            axis=1,
        )
        Temps["dsDecision"] = Temps.apply(
            lambda row: self.VMDSDecisions(row.host),
            axis=1,
        )
        Temps["isMerging"] = Temps.apply(
            lambda row: self.isMergingPoint(row.mergingPoint),
            axis=1,
        )
        Temps["isInit"] = Temps.apply(
            lambda row: self.functionsCount(row.function),
            axis=1,
        )
        TotalCostFunctions = Temps["cost"].sum()
        TotalVMexe = Temps["dsDecision"].sum()
        TotalMergings = Temps["isMerging"].sum()
        TotalInits = Temps["isInit"].sum()
        decisionInitCost = self.getDecisionInitCost(TotalInits)
        dsCost = self.VMDScost(TotalVMexe)
        mergingCost = self.mergingPointCost(TotalMergings)
        TotalCost = TotalCostFunctions + dsCost + mergingCost + decisionInitCost
        return TotalCost

    def getArrivalDict(self):
        Temps = copy.deepcopy(self.dataframe)
        startTestDate = datetime.datetime.strptime(
            (self.startTestDate), "%Y-%m-%d %H:%M:%S.%f"
        )
        dictStartT = {"startTest": ([startTestDate] * 10)}
        dfStartT = pd.DataFrame(dictStartT)
        dfStartT["startTest"] = pd.to_datetime(dfStartT["startTest"], utc=True)
        minDate = dfStartT["startTest"].min()
        # ttTemp["start"] = pd.to_datetime(ttTemp["start"], utc=True)
        # testing = ttTemp[ttTemp["start"] > minDate]
        Temps = Temps[["start", "function", "reqID"]]
        Temps["start"] = pd.to_datetime(Temps["start"], utc=True)
        Temps = Temps[Temps["start"] > minDate]
        startByReq = Temps.loc[(Temps["function"] == self.workflow_json["initFunc"])]
        startByReq = startByReq.set_index("reqID").to_dict()["start"]
        return startByReq

    def getPrevDS(self):
        prevPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/scheduler/data/"
            + "prevCost.json"
        )
        with open(prevPath, "r") as json_file:
            workflow_json = json.load(json_file)
        return workflow_json

    def functionsCount(self, function):
        if function == self.workflow_json["initFunc"]:
            return 1
        else:
            return 0

    def VMDSDecisions(self, host):
        if host != "s":
            return 1
        else:
            return 0

    def isMergingPoint(self, merging):
        if merging != None:
            return 1
        else:
            return 0

    def DSCost(self, current, mode):
        free_tier_read = 50000
        free_tier_write = 20000
        free_tier_delete = 20000
        unitRead = 0.06 / 100000
        unitWrite = 0.18 / 100000
        unitDelete = 0.02 / 100000
        prev = self.getPrevDS()
        if mode == "r":
            self.currentRead += current
        elif mode == "w":
            self.currentWrite += current
        elif mode =="d":
            self.currentDelete += current
        if mode == "r":
            # if prev["DSread"] > free_tier_read:
            #     free_tier_read = 0
            # else:
            #     free_tier_read = free_tier_read - prev["DSread"]
            cost = max(0, (self.currentRead - free_tier_read)) * unitRead
        elif mode == "w":
            
            # if prev["DSwrite"] > free_tier_write:
            #     free_tier_write = 0
            # else:
            #     free_tier_write = free_tier_write - prev["DSwrite"]
            cost = max(0, (current - free_tier_write)) * unitWrite
        elif mode == "d":
            # if prev["DSdelete"] > free_tier_delete:
            #     free_tier_delete = 0
            # else:
            #     free_tier_delete = free_tier_delete - prev["DSdelete"]
            cost = max(0, (current - free_tier_delete)) * unitDelete
        else:
            print("unknown mode!")
        return cost

    def mergingPointCost(self, mergingPoint):
        costRead = self.DSCost(mergingPoint, "r")
        costWrite = self.DSCost(mergingPoint + 1, "w")
        # ??????
        # costDelete = self.DSCost(mergingPoint, "d")
        totDScost = costWrite + costRead
        return totDScost

    def VMDScost(self, vmCount):
        costRead = self.DSCost(vmCount, "r")
        costWrite = self.DSCost(vmCount, "w")
        costDelete = self.DSCost(vmCount, "d")
        totDScost = costDelete + costWrite + costRead
        return totDScost

    def getDecisionInitCost(self, num):
        costRead = self.DSCost(num, "r")
        totDScost = costRead
        return totDScost

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
    rps = sys.argv[1]
    mode = sys.argv[2]
    x = getPlots(workflow,rps, mode)
