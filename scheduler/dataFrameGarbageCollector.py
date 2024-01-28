import json
import os
import pandas as pd
from pathlib import Path

pd.options.mode.chained_assignment = None
import configparser


class garbageCollector:
    def __init__(self, workflow):
        self.workflow = workflow
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + ".json"
        )
        dataframePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log-parser/get-workflow-logs/data/"
            + self.workflow
            + "/generatedDataFrame.pkl"
        )
        # dataframePathCSV = (
        #     str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        #     + "/log-parser/get-workflow-logs/data/"
        #     + self.workflow
        #     + "/generatedDataFrame.csv"
        # )
        # dataJsonPath = (
        #     str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        #     + "/log-parser/get-workflow-logs/data/"
        #     + self.workflow
        #     + "/data.json"
        # )

        # self.dataframe = pd.read_pickle(dataframePath)
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
            return
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        with open(dataJsonPath, "r") as json_file:
            self.dataJson = json.load(json_file)
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
        # self.windowSize = 50
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
        self.dataframe.to_pickle(dataframePath)
        self.dataframe.to_csv(dataframePathCSV)

    def selectRecords(self):
        selectedInits = self.dataframe.loc[self.dataframe["function"] == self.initFunc]
        selectedInits["start"] = pd.to_datetime(selectedInits["start"])
        selectedInits.sort_values(by=["start"], ascending=False, inplace=True)
        selectedRecords = []
        for _, record in selectedInits.iterrows():
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
                selectedRecords.append(record["reqID"])
        # print("selected::: ", selectedRecords)
        if len(selectedRecords) >= self.windowSize:
            selectedRecords = selectedRecords[: self.windowSize]
        self.finalRecodreqID = selectedRecords[-1]
        return selectedRecords

    def getLastObservations(self):
        print(self.finalRecodreqID)
        for func in self.workflowFunctions:
            # print("BEFORE::", self.dataframe.shape[0])
            selectedReq = self.dataframe.loc[
                (self.dataframe["reqID"] == self.finalRecodreqID)
                & (self.dataframe["function"] == func)
            ]
            selectedReqForFunc = selectedReq.iloc[0]["start"]
            startDate = selectedReqForFunc
            # startDate = datetime.date((selectedReqForFunc["start"])
            # self.dataframe["start"] = pd.to_datetime(
            #     self.dataframe["start"], format="%Y-%m-%d %H:%M:%S.%f"
            # )
            # self.dataframe
            selected2 = self.dataframe.loc[
                (self.dataframe["function"] == func) & (self.dataframe["host"] == "s")
            ]
            selected2["start"] = pd.to_datetime(
                selected2["start"], format="%Y-%m-%d %H:%M:%S.%f"
            )
            selected2 = selected2.loc[
                ((selected2["start"]) < startDate)
                & (~selected2["reqID"].isin(self.selectedIDs))
            ]
            # print(func, ",:::,",  selected2.index)
            self.dataframe.drop(
                selected2.index,
                inplace=True,
            )
            # print("AFTER::", self.dataframe.shape[0])
            # selected = pd.merge(self.dataframe,selected, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
            # print("func:::", func)
            # print(selected2)


if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    # workflow = "TestCaseWorkflow"
    x = garbageCollector(workflow)
    # x.getExecutionTime("vm0")
    # print(x.getFuncExecutionTime("D", "vm0", "worst-case"))
