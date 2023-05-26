import os
import json
import configparser
from pathlib import Path
from google.cloud import datastore
import pandas as pd
from getNewLogs import GetLog
import datetime
import configparser
import logging

logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__))))
    + "/logs/logParser.log",
    level=logging.INFO,
)


class dataStoreLogParser(GetLog):
    def __init__(self, workflow):
        super().__init__(workflow)
        jsonPath = (
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + self.workflow
            + ".json"
        )
        cachePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/host-agents/execution-agent/data/cachedVMData.json"
        )
        if os.path.isfile(cachePath):
            os.remove(cachePath)
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.initFunc = workflow_json["initFunc"]
        self.dictData = {}
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.windowSize = int(self.rankerConfig["windowSize"])
        startDate = str(self.rankerConfig["starttest"])
        try:
            self.startTest = datetime.datetime.strptime(
                (startDate), "%Y-%m-%d %H:%M:%S.%f"
            )
        except:
            startDate = startDate + ".0"
            self.startTest = datetime.datetime.strptime(
                (startDate), "%Y-%m-%d %H:%M:%S.%f"
            )
        # self.startTest = datetime.datetime.strptime((startDate), "%Y-%m-%d %H:%M:%S.%f")
        self.dictData["function"] = []
        self.dictData["reqID"] = []
        self.dictData["start"] = []
        self.dictData["finish"] = []
        self.dictData["mergingPoint"] = []
        self.dictData["host"] = []
        self.dictData["duration"] = []
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/key/schedulerKey.json"
        )
        configPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/project-config.ini"
        )
        globalConfig = configparser.ConfigParser()
        globalConfig.read(configPath)
        self.projectConfig = globalConfig["settings"]
        project = str(self.projectConfig["projectid"])
        self.datastore_client = datastore.Client()
        self.getNewLogs()
        self.saveNewLogs()

    def updateDataStoreCost(self, count):
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/data/"
            + "prevCost.json"
        )
        with open(jsonPath, "r") as json_file:
            prevCost_json = json.load(json_file)
        prevCost_json["DSdelete"] = prevCost_json["DSdelete"] + count
        prevCost_json["DSread"] = prevCost_json["DSread"] + count
        prevCost_json["DSwrite"] = prevCost_json["DSwrite"] + count
        with open(jsonPath, "w") as json_file:
            json.dump(prevCost_json, json_file)

    def getNewLogs(self):
        results = []
        for func in self.workflowFunctions:
            query = self.datastore_client.query(kind="vmLogs")
            query.add_filter("function", "=", func)
            results = results + list(query.fetch())
        print("num of new res:::", len(results))
        self.updateDataStoreCost(len(results))
        logInsrt = "num of new res:::" + str(len(results))
        logging.info(logInsrt)
        for res in results:
            if (res["finish"]).endswith("Z"):
                (res["finish"]) = (res["finish"])[:-1] + ".000"
            try:
                finish = datetime.datetime.strptime(
                    (res["finish"]), "%Y-%m-%d %H:%M:%S.%f"
                )
            except:
                (res["finish"]) = (res["finish"]) + ".0"
                finish = datetime.datetime.strptime(
                    (res["finish"]), "%Y-%m-%d %H:%M:%S.%f"
                )
            if (res["start"]).endswith("Z"):
                (res["start"]) = (res["start"])[:-1] + ".000"
            try:
                start = datetime.datetime.strptime(
                    (res["start"]), "%Y-%m-%d %H:%M:%S.%f"
                )
            except:
                (res["start"]) = (res["start"]) + ".0"
                start = datetime.datetime.strptime(
                    (res["start"]), "%Y-%m-%d %H:%M:%S.%f"
                )
            if start >= self.startTest:
                self.dictData["function"].append(res["function"])
                self.dictData["reqID"].append(res["reqID"])
                self.dictData["start"].append(start)
                self.dictData["finish"].append(finish)
                self.dictData["mergingPoint"].append(res["mergingPoint"])
                self.dictData["host"].append(res["host"])
                self.dictData["duration"].append(float(res["duration"]))
            log_key = self.datastore_client.key("vmLogs", res.key.id_or_name)
            self.datastore_client.delete(log_key)

    def saveNewLogs(self):
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
            newDF = self.keepWindowSize(newDataFrame)
            newDF = newDataFrame
            newDF.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".pkl"
            )
            newDF.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".csv"
            )

        else:
            newVersion = 1
            newDF = self.keepWindowSize(df)
            newDF.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/generatedDataFrame,"
                + str(newVersion)
                + ".pkl"
            )
            newDF.to_csv(
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
            initRecords = df.loc[(df["function"] == self.initFunc)]
            initRecords = initRecords["start"]
            print(initRecords)
            initRecords.to_pickle(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates.pkl"
            )
            initRecords.to_csv(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + self.workflow
                + "/invocationRates.csv"
            )

    def keepWindowSize(self, df):
        serverlessDF = df.loc[df["host"] == "s"]
        df.drop(
            df[(df["host"] == "s")].index,
            inplace=True,
        )
        df["start"] = pd.to_datetime(df["start"], utc=True)
        df.sort_values(by=["start"], ascending=False, inplace=True)
        vmSelectedDF = df.groupby(["host", "function"]).head(self.windowSize)
        finalDF = (
            pd.concat([serverlessDF, vmSelectedDF])
            .drop_duplicates()
            .reset_index(drop=True)
        )
        return finalDF


if __name__ == "__main__":
    path = (
        str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
        + "/scheduler/rankerConfig.ini"
    )
    config = configparser.ConfigParser()
    config.read(path)
    rankerConfig = config["settings"]
    workflow = rankerConfig["workflow"]
    x = dataStoreLogParser(workflow)
