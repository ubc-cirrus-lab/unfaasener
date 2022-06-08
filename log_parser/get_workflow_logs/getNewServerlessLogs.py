from re import X
import subprocess
import json
import shlex
import datetime
from sys import getsizeof
import time
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import math
import pandas as pd
from pathlib import Path
from getNewLogs import GetLog


class getNewLogs(GetLog):
    def __init__(self, workflow):
        super().__init__(workflow)
        self.exeData = {}
        self.dictData = {}
        self.windowSize = 50
        self.dictData["function"] = []
        self.dictData["reqID"] = []
        self.dictData["start"] = []
        self.dictData["finish"] = []
        self.dictData["mergingPoint"] = []
        self.dictData["host"] = []
        self.dictData["duration"] = []
        self.NI = 0
        self.GBSec = 0
        self.GHzSec = 0
        self.writeLogs = {}
        with open(os.getcwd() + "/data/" + workflow + ".json", "r") as json_file:
            workflow_json = json.load(json_file)
        self.initFunc = workflow_json["initFunc"]
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.predecessors = workflow_json["predecessors"]
        self.memories = workflow_json["memory"]
        for func in self.workflowFunctions:
            self.writeLogs[func] = []
        self.lastTimestamp = None
        # self.checkLatestTimeStamp()
        for func in self.workflowFunctions:
            self.checkLatestTimeStamp(func)
            self.pullLogs(func)
        with open(
            (os.getcwd() + "/data/" + str(self.workflow) + "/" + "data.json"), "w"
        ) as outfile:
            json.dump(self.writeLogs, outfile)
        self.getDict()
        self.saveCost()

    def saveCost(self):
        jsonPath = (
            str(Path(os.getcwd()).resolve().parents[1])
            + "/scheduler/data/"
            + self.workflow
            + "-prevCost.json"
        )
        with open(jsonPath, "r") as json_file:
            prevCost_json = json.load(json_file)
        prevCost_json["GB-Sec"] = prevCost_json["GB-Sec"] + self.GBSec
        prevCost_json["GHz-Sec"] = prevCost_json["GHz-Sec"] + self.GHzSec
        prevCost_json["NI"] = prevCost_json["NI"] + self.NI
        with open(jsonPath, "w") as json_file:
            json.dump(prevCost_json, json_file)

    def checkLatestTimeStamp(self, func):
        if os.path.isfile(
            os.getcwd() + "/data/" + str(self.workflow) + "/" + "data.json"
        ):
            with open(
                os.getcwd() + "/data/" + str(self.workflow) + "/" + "data.json", "r"
            ) as outfile:
                workflow_json = json.load(outfile)
                lastRecordedTimestamp = str(workflow_json[func][0]["time_utc"])
                arrayTS = lastRecordedTimestamp.split()
                self.lastTimestamp = arrayTS[0] + "T" + arrayTS[1]
                print("TT::::", self.lastTimestamp)
                self.writeLogs = workflow_json

    def pullLogs(self, function):
        if self.lastTimestamp != None:
            endFlag = False
            while endFlag != True:
                lastLog = (
                    "gcloud functions logs read "
                    + function
                    + " --region northamerica-northeast1 --format json --limit 1 "
                )
                lastLog_logs = subprocess.check_output(shlex.split(lastLog))
                lastLog_logs_json = json.loads(lastLog_logs)
                lastLog_date = [
                    element["time_utc"] for idx, element in enumerate(lastLog_logs_json)
                ]
                lastLogEndDate = lastLog_date[0]
                arrayLLET = lastLogEndDate.split()
                timeLast = arrayLLET[1]
                lastDigit = int(timeLast[-1])
                timeLast = timeLast[:-1]
                timeLast = timeLast + str(lastDigit + 1)
                lastLogEndDate = arrayLLET[0] + "T" + timeLast
                project_list_logs = (
                    "gcloud functions logs read "
                    + function
                    + " --region northamerica-northeast1 --format json "
                    + "--start-time "
                    + self.lastTimestamp
                    + " --end-time "
                    + lastLogEndDate
                    + " --limit 1000"
                )
                project_logs = subprocess.check_output(shlex.split(project_list_logs))
                project_logs_json = json.loads(project_logs)
                prevData = self.writeLogs[function]
                project_logs_json = [
                    x for x in project_logs_json if x not in (self.writeLogs[function])
                ]
                (self.writeLogs[function]) = project_logs_json + (
                    self.writeLogs[function]
                )
                print("PREVV:::", len(prevData))
                print("NEWW:::", len(project_logs_json))
                print("LENN:::", len(self.writeLogs[function]))
                ids = [
                    idx
                    for idx, element in enumerate(self.writeLogs[function])
                    if ("finished with status" in element["log"])
                ]
                newInvocations = [
                    idx
                    for idx, element in enumerate(project_logs_json)
                    if ("finished with status" in element["log"])
                ]
                numNewInvocations = len(newInvocations)
                self.NI += numNewInvocations
                if (self.writeLogs[function]) == prevData:
                    endFlag = True
                with open(
                    (os.getcwd() + "/data/" + str(self.workflow) + "/" + "data.json"),
                    "w",
                ) as outfile:
                    json.dump(self.writeLogs, outfile)
                self.checkLatestTimeStamp(function)
        else:
            project_list_logs = (
                "gcloud functions logs read "
                + function
                + " --region northamerica-northeast1 --format json --limit 1000"
            )
            project_logs = subprocess.check_output(shlex.split(project_list_logs))
            project_logs_json = json.loads(project_logs)
            (self.writeLogs[function]).extend(project_logs_json)
            ids = [
                idx
                for idx, element in enumerate(self.writeLogs[function])
                if ("finished with status" in element["log"])
            ]
            newInvocations = [
                idx
                for idx, element in enumerate(project_logs_json)
                if ("finished with status" in element["log"])
            ]
            numNewInvocations = len(newInvocations)
            self.NI += numNewInvocations

    def addCost(self, mem, dur):
        if mem == 0.128:
            Ghz = 0.2
        elif mem == 0.256:
            Ghz = 0.4
        elif mem == 0.512:
            Ghz = 0.8
        elif mem == 1:
            Ghz = 1.4
        elif mem == 2:
            Ghz = 2.4
        elif mem == 4:
            Ghz = 4.8
        elif mem == 8:
            Ghz = 4.8
        self.GBSec += mem * dur
        self.GHzSec += Ghz * dur

    def getDict(self):
        self.dictData
        with open(
            os.getcwd() + "/data/" + str(self.workflow) + "/" + "data.json", "r"
        ) as outfile:
            workflow_json = json.load(outfile)
        for func in self.workflowFunctions:
            # matchingDict = {}
            funcData = workflow_json[func]
            startLogs = [
                element["execution_id"]
                for idx, element in enumerate(funcData)
                if ("Function execution started" in element["log"])
            ]
            startTimes = [
                element["time_utc"]
                for idx, element in enumerate(funcData)
                if ("Function execution started" in element["log"])
            ]
            reqIDs = [
                element["log"].split("*")[0].replace("WARNING:root:", "")
                for idx, element in enumerate(funcData)
                if ("WARNING:root:" in element["log"])
            ]
            mergeData = [
                element["log"]
                for idx, element in enumerate(funcData)
                if ("WARNING:root:" in element["log"])
            ]
            reqLogs = [
                element["execution_id"]
                for idx, element in enumerate(funcData)
                if ("WARNING:root:" in element["log"])
            ]
            finishLogs = [
                element["execution_id"]
                for idx, element in enumerate(funcData)
                if (
                    ("finished with status" in element["log"])
                    or ("Finished with status" in element["log"])
                )
            ]
            finishTimes = [
                element["time_utc"]
                for idx, element in enumerate(funcData)
                if (
                    ("finished with status" in element["log"])
                    or ("Finished with status" in element["log"])
                )
            ]
            # sortingArray = startTimes
            # for e in range(len(startLogs)):
            #     matchingDict[startTimes[startLogs.index(startLogs[e])]] = startLogs[e]

            # sortingArray.sort(key=lambda date: datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f"))
            # # matchingDict = sorted(matchingDict.items(), key = lambda x:datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
            # sortingArray = sortingArray[(-self.windowSize):]
            # sortedIDs = []
            # for date in sortingArray:
            #     sortedIDs.append(matchingDict[date])
            for exe in startLogs:
                if (exe in finishLogs) and (exe in reqLogs):
                    self.dictData["host"].append("s")
                    self.dictData["function"].append(func)
                    self.dictData["reqID"].append(reqIDs[reqLogs.index(exe)])
                    if (finishTimes[finishLogs.index(exe)]).endswith("Z"):
                        (finishTimes[finishLogs.index(exe)]) = (
                            finishTimes[finishLogs.index(exe)]
                        )[:-1] + ".000"
                    finish = datetime.datetime.strptime(
                        (finishTimes[finishLogs.index(exe)]), "%Y-%m-%d %H:%M:%S.%f"
                    )
                    self.dictData["finish"].append(finish)
                    if (startTimes[startLogs.index(exe)]).endswith("Z"):
                        (startTimes[startLogs.index(exe)]) = (
                            startTimes[startLogs.index(exe)]
                        )[:-1] + ".000"
                    start = datetime.datetime.strptime(
                        (startTimes[startLogs.index(exe)]), "%Y-%m-%d %H:%M:%S.%f"
                    )
                    self.dictData["start"].append(start)
                    self.dictData["duration"].append(
                        ((finish - start).total_seconds()) * 1000
                    )
                    self.addCost(
                        self.memories[self.workflowFunctions.index(func)],
                        (
                            math.ceil((((finish - start).total_seconds()) * 1000) / 100)
                            * 0.1
                        ),
                    )
                    if len(self.predecessors[self.workflowFunctions.index(func)]) <= 1:
                        self.dictData["mergingPoint"].append(None)
                    else:
                        mergingBranch = ((mergeData[reqLogs.index(exe)]).split("*"))[1]
                        self.dictData["mergingPoint"].append(mergingBranch)
        df = pd.DataFrame(self.dictData)
        if os.path.isfile(
            os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
        ):
            prevDataframe = pd.read_pickle(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDataFrame = (
                pd.concat([prevDataframe, df]).drop_duplicates().reset_index(drop=True)
            )
            newDataFrame.to_pickle(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDataFrame.to_csv(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.csv"
            )

        else:
            print(df.shape[0])
            df.to_pickle(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            df.to_csv(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.csv"
            )


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    workflow = "Text2SpeechCensoringWorkflow"
    x = getNewLogs(workflow)
