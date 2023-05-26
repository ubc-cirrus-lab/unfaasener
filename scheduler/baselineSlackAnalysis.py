import json
import os
import pandas as pd
import numpy as np
from criticalpath import Node
from pathlib import Path

# import rankerConfig
import configparser
import statistics
import functools
import operator

pd.options.mode.chained_assignment = None


class baselineSlackAnalysisClass:
    def __init__(self, workflow):
        self.workflow = workflow
        # jsonPath = os.getcwd() + "/log-parser/get-workflow-logs/data/" + self.workflow+".json"
        # dataframePath = os.getcwd() + "/log-parser/get-workflow-logs/data/" + self.workflow + "/NEWWgeneratedData.pkl"
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + ".json"
        )
        # dataframePath = str(Path(os.getcwd()).resolve().parents[0]) + "/log-parser/get-workflow-logs/data/" + self.workflow + "/generatedDataFrame.pkl"
        dfDir = Path(
            str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
            + "/log-parser/get-workflow-logs/data/"
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
        #     str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
        #     + "/log-parser/get-workflow-logs/data/"
        #     + self.workflow
        #     + "/generatedDataFrame.pkl"
        # ):
        if len(dfFilesNames) != 0:
            dfFilesNames = [a.replace(".pkl", "") for a in dfFilesNames]
            versions = [int((a.split(","))[1]) for a in dfFilesNames]
            lastVersion = max(versions)
            dataframePath = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[0]
                )
                + "/log-parser/get-workflow-logs/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(lastVersion)
                + ".pkl"
            )
            self.dataframe = pd.read_pickle(dataframePath)
        elif os.path.isfile(
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + "/generatedDataFrame.csv"
        ):
            dataframePath = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[0]
                )
                + "/log-parser/get-workflow-logs/data/"
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
        self.recordNum = 0
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.windowSize = int(self.rankerConfig["windowSize"])
        self.slackData = {}
        self.dependencies = []
        self.recordNum = len(self.workflowFunctions)
        for func in self.workflowFunctions:
            self.slackData[func] = []
            for i in self.successors[self.workflowFunctions.index(func)]:
                self.slackData[func + "-" + i] = []
                self.dependencies.append((func, (func + "-" + i)))
                self.dependencies.append(((func + "-" + i), i))
            if len(self.predecessors[self.workflowFunctions.index(func)]) > 1:
                self.recordNum += (
                    len(self.predecessors[self.workflowFunctions.index(func)])
                ) - 1
        self.memories = workflow_json["memory"]
        # self.dataframe = pd.read_pickle(dataframePath)
        self.selectedIDs = self.selectRecords()
        self.observations = self.getObservations()
        self.slackCalculations()
        with open(path, "w") as configfile:
            self.config.write(configfile)

    # def getCriticalPathDuration(self):
    #     return self.duration
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
            # newMergingPatternChanges
            createdSet = selectedReq["function"].copy()
            createdSet = set(createdSet.to_numpy())
            if (selectedReq.shape[0] >= self.recordNum) and (
                len(createdSet) == len(self.workflowFunctions)
            ):
                # if selectedReq.shape[0] >= self.recordNum:
                selectedRecords.append(record["reqID"])
        if len(selectedRecords) >= self.windowSize:
            selectedRecords = selectedRecords[: self.windowSize]
        # print("SELECTEDRECORDS::::", selectedRecords)
        return selectedRecords

    def getObservations(self):
        for func in self.workflowFunctions:
            # newMergingPatternChanges
            for reqID in self.selectedIDs:
                df2 = self.dataframe.loc[
                    (
                        (self.dataframe["reqID"] == reqID)
                        & (self.dataframe["function"] == func)
                    )
                ]
                if df2.shape[0] == 1:
                    # merging = self.dataframe.loc[((self.dataframe["reqID"] == reqID) & (self.dataframe["function"] == func)), "mergingPoint"]
                    # if merging == None:
                    selectedDuration = df2.iloc[0]["duration"]
                    self.slackData[func].append(selectedDuration)
                    # self.dataframe.loc[((self.dataframe["reqID"] == reqID) & (self.dataframe["function"] == func)), "duration"]
                elif len(self.predecessors[self.workflowFunctions.index(func)]) > 1:
                    start = df2["start"].max()
                    finish = df2["finish"].max()
                    duration = ((finish - start).total_seconds()) * 1000
                    self.slackData[func].append(duration)
                else:
                    duration = df2["duration"].mean()
                    self.slackData[func].append(duration)
        for entry in self.slackData.keys():
            # newMergingPatternChanges
            if entry not in self.workflowFunctions:
                for reqID in self.selectedIDs:
                    prevFunc = entry.split("-")[0]
                    nextFunc = entry.split("-")[1]
                    dfPrev = self.dataframe.loc[
                        (
                            (self.dataframe["reqID"] == reqID)
                            & (self.dataframe["function"] == prevFunc)
                        )
                    ]
                    dfNext = self.dataframe.loc[
                        (
                            (self.dataframe["reqID"] == reqID)
                            & (self.dataframe["function"] == nextFunc)
                        )
                    ]
                    if dfPrev.shape[0] == 1:
                        finish = dfPrev.iloc[0]["finish"]
                    elif (
                        len(self.predecessors[self.workflowFunctions.index(prevFunc)])
                        > 1
                    ):
                        finish = dfPrev["finish"].max()
                    else:
                        start = self.avg_datetime(dfNext["start"])
                    if dfNext.shape[0] == 1:
                        start = dfNext.iloc[0]["start"]
                    elif (
                        len(self.predecessors[self.workflowFunctions.index(nextFunc)])
                        > 1
                    ):
                        start = dfNext.loc[dfNext["mergingPoint"] == prevFunc].iloc[0][
                            "start"
                        ]
                    else:
                        start = self.avg_datetime(dfNext["start"])
                        # start = dfNext.loc[dfNext["mergingPoint"] == prevFunc].iloc[0][
                        #     "start"
                        # ]

                    duration = ((start - finish).total_seconds()) * 1000
                    self.slackData[entry].append(duration)

    # newMergingPatternChanges
    def avg_datetime(self, series):
        dt_min = series.min()
        deltas = [x - dt_min for x in series]
        return dt_min + functools.reduce(operator.add, deltas) / len(deltas)

    def getUpperBound(self, array):
        n = len(array)
        if n <= 30:
            upperBound = np.percentile(array, 75)
        else:
            sortedArray = np.sort(array)
            z = 1.96
            index = int(np.ceil(1 + ((n + (z * (np.sqrt(n)))) / 2)))
            upperBound = sortedArray[index]
        return upperBound

    def getMedian(self, array):
        # median = array.quantile(0.5)

        median = statistics.median(array)
        statistics.quantiles
        return median

    def getLowerBound(self, array):
        n = len(array)
        if n <= 30:
            lowerBound = np.percentile(array, 25)
        else:
            sortedArray = np.sort(array)
            z = 1.96
            index = int(np.floor((n - (z * (np.sqrt(n)))) / 2))
            lowerBound = sortedArray[index]
        return lowerBound

    def findCriticalPath(self, tasks, dependencies):
        workflow = Node("Workflow")
        for task in tasks:
            workflow.add(Node(task, duration=tasks[task]))
        for dependency in dependencies:
            workflow.link(dependency[0], dependency[1])
        workflow.update_all()
        criticalPath = [str(node) for node in workflow.get_critical_path()]
        workflowDuration = workflow.duration
        return workflowDuration, criticalPath

    def completeESEF(self, initial):
        self.es[initial] = 0
        self.ef[initial] = self.tasks[initial]
        nextSteps = []
        for d in self.dependencies:
            if d[0] == initial:
                if d[1] in self.es:
                    self.es[d[1]] = max(self.es[d[1]], self.ef[initial])
                    self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                else:
                    self.es[d[1]] = self.ef[initial]
                    self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                nextSteps.append(d[1])
        for n in nextSteps:
            initial = n
            for d in self.dependencies:
                if d[0] == initial:
                    if d[1] in self.es:
                        self.es[d[1]] = max(self.es[d[1]], self.ef[initial])
                        self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                    else:
                        self.es[d[1]] = self.ef[initial]
                        self.ef[d[1]] = self.es[d[1]] + self.tasks[d[1]]
                    nextSteps.append(d[1])

    def completeLSLF(self, duration, criticalPath):
        terminals = []
        for d in self.dependencies:
            terminalFlag = True
            for d2 in self.dependencies:
                if d[1] == d2[0]:
                    terminalFlag = False
                    break
            if terminalFlag == True:
                terminals.append(d[1])
        for t in terminals:
            self.lf[t] = duration
            self.ls[t] = duration - self.tasks[t]

        for t in terminals:
            for d in self.dependencies:
                if d[1] == t:
                    if d[0] in self.lf:
                        self.lf[d[0]] = min(self.lf[d[0]], self.ls[t])
                        self.ls[d[0]] = max(0, self.lf[d[0]] - self.tasks[d[0]])
                    else:
                        self.lf[d[0]] = self.ls[t]
                        self.ls[d[0]] = max(0, self.lf[d[0]] - self.tasks[d[0]])

                    terminals.append(d[0])

    def slackCalculations(self):
        slackResults = {}
        slackDurations = {}
        for col in self.slackData.keys():
            slackResults[col] = {}
            slackDurations[col] = {}

        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        config = configparser.ConfigParser()
        config.read(path)
        rankerConfig = config["settings"]
        decisionModes = rankerConfig["decisionMode"].split()
        for decisionMode in decisionModes:
            self.tasks = {}
            self.es = {}
            self.ef = {}
            self.ls = {}
            self.lf = {}
            for col in self.slackData.keys():
                if decisionMode == "best-case":
                    self.tasks[col] = self.getUpperBound(self.slackData[col])
                elif decisionMode == "worst-case":
                    self.tasks[col] = self.getLowerBound(self.slackData[col])
                elif decisionMode == "default":
                    self.tasks[col] = self.getMedian(self.slackData[col])
                else:
                    self.tasks[col] = self.getMedian(self.slackData[col])
                slackDurations[col][decisionMode] = self.tasks[col]
            self.duration, self.crPath = self.findCriticalPath(
                self.tasks, self.dependencies
            )
            if decisionMode == "default":
                multipliedParam = 1
                self.rankerConfig["tolerancewindow"] = str(
                    multipliedParam * (int(self.duration))
                )
            self.completeESEF(self.initFunc)
            self.completeLSLF(self.duration, self.crPath)
            for col in self.slackData.keys():
                slack = self.lf[col] - self.ef[col]
                slackResults[col][decisionMode] = slack
        # print(slackResults)
        with open(
            (
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + "slackData.json"
            ),
            "w",
            os.O_NONBLOCK,
        ) as outfile:
            json.dump(slackResults, outfile)
        with open(
            (
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + "slackDurations.json"
            ),
            "w",
            os.O_NONBLOCK,
        ) as outfile:
            json.dump(slackDurations, outfile)


if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = "TestCaseWorkflow"

    x = baselineSlackAnalysisClass(workflow)
