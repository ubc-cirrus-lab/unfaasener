import subprocess
import json
import shlex
import datetime
import os
import math
import pandas as pd
from pathlib import Path
from getNewLogs import GetLog
import configparser
import copy
import logging

logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__))))
    + "/logs/logParser.log",
    level=logging.INFO,
)


class getNewLogs(GetLog):
    def __init__(self, workflow):
        super().__init__(workflow)
        self.exeData = {}
        self.dictData = {}
        self.dataStoreCount = 0
        self.readDecisionCount = 0
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.windowSize = int(self.rankerConfig["windowSize"])
        # self.windowSize = 50
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
        with open(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + workflow
            + ".json",
            "r",
        ) as json_file:
            workflow_json = json.load(json_file)
        self.initFunc = workflow_json["initFunc"]
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.predecessors = workflow_json["predecessors"]
        self.memories = workflow_json["memory"]
        for func in self.workflowFunctions:
            self.writeLogs[func] = []
        self.newTimeStampRecorded = {}
        self.tempTimeStampRecorded = {}
        # self.checkLatestTimeStamp()
        if os.path.isfile(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + "prevData.json"
        ):
            with open(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + "prevData.json",
                "r",
                os.O_NONBLOCK,
            ) as outfile:
                self.prevData = json.load(outfile)
        else:
            self.prevData = {}
            for func in self.workflowFunctions:
                self.prevData[func] = []
        for func in self.workflowFunctions:
            self.lastTimestamp = None
            self.checkLatestTimeStamp(func)
            self.pullLogs(func)
        # with open(
        #     (
        #         (os.path.dirname(os.path.abspath(__file__)))
        #         + "/data/"
        #         + str(self.workflow)
        #         + "/"
        #         + "data.json"
        #     ),
        #     "w", os.O_NONBLOCK
        # ) as outfile:
        #     json.dump(self.newTimeStampRecorded, outfile)
        self.getDict()
        self.saveCost()

    def saveCost(self):
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/data/"
            + "prevCost.json"
        )
        with open(jsonPath, "r") as json_file:
            prevCost_json = json.load(json_file)
        prevCost_json["GB-Sec"] = prevCost_json["GB-Sec"] + self.GBSec
        prevCost_json["GHz-Sec"] = prevCost_json["GHz-Sec"] + self.GHzSec
        prevCost_json["NI"] = prevCost_json["NI"] + self.NI
        prevCost_json["DSread"] = (
            prevCost_json["DSread"] + self.dataStoreCount + self.readDecisionCount
        )
        prevCost_json["DSwrite"] = prevCost_json["DSwrite"] + self.dataStoreCount
        with open(jsonPath, "w") as json_file:
            json.dump(prevCost_json, json_file)

    def checkLatestTimeStamp(self, func):
        if os.path.isfile(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + "data.json"
        ):
            with open(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + "data.json",
                "r",
                os.O_NONBLOCK,
            ) as outfile:
                workflow_json = json.load(outfile)
                self.newTimeStampRecorded = copy.deepcopy(workflow_json)
                self.tempTimeStampRecorded = copy.deepcopy(workflow_json)
                if func in workflow_json.keys():
                    lastRecordedTimestamp = str(workflow_json[func])
                    # lastRecordedTimestamp = str(workflow_json[func][0]["time_utc"]
                    arrayTS = lastRecordedTimestamp.split()
                    self.lastTimestamp = arrayTS[0] + "T" + arrayTS[1]
                    print("TT::::", self.lastTimestamp)
                    # self.writeLogs = workflow_json

    def pullLogs(self, function):
        if self.lastTimestamp != None:
            lastLog = (
                "gcloud functions logs read "
                + function
                + " --region northamerica-northeast1 --format json --limit 1 "
            )
            lastLog_logs = subprocess.check_output(shlex.split(lastLog))
            lastLog_logs_json = json.loads(lastLog_logs)
            # if len(lastLog_logs_json) == 0:
            #     endFlag = True
            #     break
            lastLog_date = [
                element["time_utc"] for idx, element in enumerate(lastLog_logs_json)
            ]
            # lastLogEndDate = datetime.datetime.strptime(
            #         lastLog_date[0], "%Y-%m-%d %H:%M:%S.%f"
            #     )
            # # lastLogEndDate = lastLogEndDate + timedelta(milliseconds=1)
            # lastLogEndDate = lastLogEndDate.strftime("%Y-%m-%d %H:%M:%S.%f")
            # arrayLLET = lastLogEndDate.split()
            # lastLogEndDate = arrayLLET[0] + "T" + arrayLLET[1]
            # !!!!!!!!!!
            # self.newTimeStampRecorded[function] = lastLogEndDate
            self.tempTimeStampRecorded[function] = lastLog_date[0]
            print("Time for  func: ", function, " is::", lastLog_date[0])
            endFlag = False
            while endFlag is False:
                tempDate = datetime.datetime.strptime(
                    self.tempTimeStampRecorded[function], "%Y-%m-%d %H:%M:%S.%f"
                )
                # lastLogEndDate = lastLogEndDate + timedelta(milliseconds=1)
                tempDate = tempDate.strftime("%Y-%m-%d %H:%M:%S.%f")
                arrayLLET = tempDate.split()
                tempDateEnd = arrayLLET[0] + "T" + arrayLLET[1]
                arrayStart = self.newTimeStampRecorded[function].split()
                NewStartDate = arrayStart[0] + "T" + arrayStart[1]
                project_list_logs = (
                    "gcloud functions logs read "
                    + function
                    + " --region northamerica-northeast1 --format json "
                    + "--start-time "
                    + NewStartDate
                    + " --end-time "
                    + tempDateEnd
                    + " --limit 1000"
                )
                project_logs = subprocess.check_output(shlex.split(project_list_logs))
                project_logs_json_old = json.loads(project_logs)
                # if len(project_logs_json) == 0:
                #     endFlag = True
                #     break
                prevData = copy.deepcopy(self.writeLogs[function])
                project_logs_json = [
                    x for x in project_logs_json_old if x not in (prevData)
                ]
                (self.writeLogs[function]) = project_logs_json + (prevData)
                print("PREVV:::", len(prevData))
                print("RETRIEVED::::::", len(project_logs_json_old))
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
                # if len(self.writeLogs[function]) != 0:
                #     self.newTimeStampRecorded[function] = str(
                #         self.writeLogs[function][0]["time_utc"]
                #     )
                if len(project_logs_json) == 0:
                    # if(len(self.writeLogs[function]) != 0):
                    #     self.newTimeStampRecorded[function] = str(self.writeLogs[function][0]["time_utc"])
                    endFlag = True
                if len(project_logs_json_old) != 0:
                    self.tempTimeStampRecorded[function] = str(
                        project_logs_json_old[-1]["time_utc"]
                    )
            # self.newTimeStampRecorded[function] = lastLog_date[0]
            # with open(
            #         (
            #             (os.path.dirname(os.path.abspath(__file__)))
            #             + "/data/"
            #             + str(self.workflow)
            #             + "/"
            #             + "data.json"
            #         ),
            #         "w", os.O_NONBLOCK
            #     ) as outfile:
            #         json.dump(self.newTimeStampRecorded, outfile)
            # self.checkLatestTimeStamp(function)
        else:
            "No data file!"
            # project_list_logs = (
            #     "gcloud functions logs read "
            #     + function
            #     + " --region northamerica-northeast1 --format json --limit 1000"
            # )
            # project_logs = subprocess.check_output(shlex.split(project_list_logs))
            # project_logs_json = json.loads(project_logs)
            # (self.writeLogs[function]).extend(project_logs_json)
            # ids = [
            #     idx
            #     for idx, element in enumerate(self.writeLogs[function])
            #     if ("finished with status" in element["log"])
            # ]
            # newInvocations = [
            #     idx
            #     for idx, element in enumerate(project_logs_json)
            #     if ("finished with status" in element["log"])
            # ]
            # numNewInvocations = len(newInvocations)
            # self.newTimeStampRecorded[function] = str(
            #     self.writeLogs[function][0]["time_utc"]
            # )
            # with open(
            #     (
            #         (os.path.dirname(os.path.abspath(__file__)))
            #         + "/data/"
            #         + str(self.workflow)
            #         + "/"
            #         + "data.json"
            #     ),
            #     "w",
            # ) as outfile:
            #     json.dump(self.newTimeStampRecorded, outfile)
            # self.NI += numNewInvocations

    def addCost(self, mem, dur):
        if mem == 0.125:
            Ghz = 0.2
        elif mem == 0.25:
            Ghz = 0.4
        elif mem == 0.5:
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
        # self.dictData
        # with open(
        #     (os.path.dirname(os.path.abspath(__file__))) + "/data/" + str(self.workflow) + "/" + "data.json", "r"
        # ) as outfile:
        #     workflow_json = json.load(outfile)
        workflow_json = self.writeLogs
        for func in self.workflowFunctions:
            # matchingDict = {}
            funcData = workflow_json[func] + self.prevData[func]
            startLogsTot = [
                (element["execution_id"], idx)
                for idx, element in enumerate(funcData)
                if ("Function execution started" in element["log"])
            ]
            startLogs = [i[0] for i in startLogsTot]
            startLogsIndex = [i[1] for i in startLogsTot]

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
            reqLogsTot = [
                (element["execution_id"], idx)
                for idx, element in enumerate(funcData)
                if ("WARNING:root:" in element["log"])
            ]
            reqLogs = [i[0] for i in reqLogsTot]
            reqLogsIndex = [i[1] for i in reqLogsTot]

            finishLogsTot = [
                (element["execution_id"], idx)
                for idx, element in enumerate(funcData)
                if (
                    (
                        ("finished with status" in element["log"])
                        or ("Finished with status" in element["log"])
                    )
                    and ("crash" not in element["log"])
                )
            ]
            finishLogs = [i[0] for i in finishLogsTot]
            finishLogsIndex = [i[1] for i in finishLogsTot]
            finishTimes = [
                element["time_utc"]
                for idx, element in enumerate(funcData)
                if (
                    (
                        ("finished with status" in element["log"])
                        or ("Finished with status" in element["log"])
                    )
                    and ("crash" not in element["log"])
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
            deleteStartList = []
            deleteFinishList = []
            deleteReqList = []
            for exe in startLogs:
                if (exe in finishLogs) and (exe in reqLogs):
                    deleteStartList.append(startLogs.index(exe))
                    deleteFinishList.append(finishLogs.index(exe))
                    deleteReqList.append(reqLogs.index(exe))
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
                        self.dataStoreCount = self.dataStoreCount + 1
                    # del startLogsIndex[startLogs.index(exe)]
                    # del reqLogsIndex[reqLogs.index(exe)]
                    # del finishLogsIndex[finishLogs.index(exe)]
            for index in sorted(list(set(deleteStartList)), reverse=True):
                del startLogsIndex[index]
            for index in sorted(list(set(deleteFinishList)), reverse=True):
                del finishLogsIndex[index]
            for index in sorted(list(set(deleteReqList)), reverse=True):
                del reqLogsIndex[index]
            self.prevData[func] = (
                [funcData[i] for i in startLogsIndex]
                + [funcData[i] for i in reqLogsIndex]
                + [funcData[i] for i in finishLogsIndex]
            )
        df = pd.DataFrame(self.dictData)
        dfDir = Path(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + self.workflow
            + "/"
        )
        dfFilesNames = [
            file.name
            for file in dfDir.iterdir()
            if (
                (file.name.startswith("generatedDataFrame"))
                and (file.name.endswith(".pkl"))
            )
        ]
        # if os.path.isfile(
        #     (os.path.dirname(os.path.abspath(__file__)))
        #     + "/data/"
        #     + self.workflow
        #     + "/generatedDataFrame,"+str(lastVersion)+".pkl"
        # ):
        if len(dfFilesNames) != 0:
            dfFilesNames = [a.replace(".pkl", "") for a in dfFilesNames]
            versions = [int((a.split(","))[1]) for a in dfFilesNames]
            lastVersion = max(versions)
            newVersion = lastVersion + 1
            prevDataframe = pd.read_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(lastVersion)
                + ".pkl"
            )
            newDataFrame = (
                pd.concat([prevDataframe, df]).drop_duplicates().reset_index(drop=True)
            )
            newDataFrame.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".pkl"
            )
            newDataFrame.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".csv"
            )

        else:
            newVersion = 1
            print(df.shape[0])
            df.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".pkl"
            )
            df.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".csv"
            )
        invocationFilesNames = [
            file.name
            for file in dfDir.iterdir()
            if (
                (file.name.startswith("invocationRates"))
                and (file.name.endswith(".pkl"))
            )
        ]
        # if os.path.isfile(
        #     (os.path.dirname(os.path.abspath(__file__)))
        #     + "/data/"
        #     + self.workflow
        #     + "/invocationRates.pkl"
        # ):
        if len(invocationFilesNames) != 0:
            invocationFilesNames = [a.replace(".pkl", "") for a in invocationFilesNames]
            versions = [int((a.split(","))[1]) for a in invocationFilesNames]
            lastVersion = max(versions)
            newVersion = lastVersion + 1
            prevInvocations = pd.read_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates,"
                + str(lastVersion)
                + ".pkl"
            )
            initRecords = df.loc[(df["function"] == self.initFunc)]
            initRecords = initRecords["start"]
            self.readDecisionCount = self.readDecisionCount + len(initRecords)

            newInvocations = (
                pd.concat([prevInvocations, initRecords])
                .drop_duplicates()
                .reset_index(drop=True)
            )
            print(newInvocations)
            newInvocations.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates,"
                + str(newVersion)
                + ".pkl"
            )
            newInvocations.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates,"
                + str(newVersion)
                + ".csv"
            )

        else:
            newVersion = 1
            initRecords = df.loc[(df["function"] == self.initFunc)]
            initRecords = initRecords["start"]
            print(initRecords)
            initRecords.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates,"
                + str(newVersion)
                + ".pkl"
            )
            initRecords.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates,"
                + str(newVersion)
                + ".csv"
            )
        with open(
            (
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + "prevData.json"
            ),
            "w",
            os.O_NONBLOCK,
        ) as outfile:
            json.dump(self.prevData, outfile)


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    workflow = "Text2SpeechCensoringWorkflow"
    x = getNewLogs(workflow)
