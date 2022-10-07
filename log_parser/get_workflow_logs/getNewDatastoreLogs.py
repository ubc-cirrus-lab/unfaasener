import time
import numpy as np
import os
import json
from pathlib import Path
from google.cloud import datastore
import pandas as pd
from getNewLogs import GetLog
import datetime
import configparser
import logging
logging.basicConfig(filename=str(Path(os.path.dirname(os.path.abspath(__file__))))+"/logs/logParser.log", level=logging.INFO)



class dataStoreLogParser(GetLog):
    def __init__(self, workflow):
        super().__init__(workflow)
        jsonPath = (
            (os.path.dirname(os.path.abspath(__file__))) +
            "/data/"
            + self.workflow
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.initFunc = workflow_json["initFunc"]
        self.dictData = {}
        # self.windowSize = 50
        path = str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])+ "/scheduler/rankerConfig.ini"
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        self.windowSize = int(self.rankerConfig["windowSize"])
        startDate = str(self.rankerConfig["starttest"])
        self.startTest = datetime.datetime.strptime((startDate), "%Y-%m-%d %H:%M:%S.%f")
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
        project = "ubc-serverless-ghazal"
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
        logInsrt = "num of new res:::" +  str(len(results))
        logging.info(logInsrt)
        for res in results:
            if (res["finish"]).endswith("Z"):
                        (res["finish"]) = (
                            res["finish"]
                        )[:-1] + ".000"
            finish = datetime.datetime.strptime(
                        (res["finish"]), "%Y-%m-%d %H:%M:%S.%f"
                    )
            if (res["start"]).endswith("Z"):
                        (res["start"]) = (
                            res["start"]
                        )[:-1] + ".000"
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
        if os.path.isfile(
            (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.pkl"
        ):

            prevDataframe = pd.read_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDataFrame = (
                pd.concat([prevDataframe, df]).drop_duplicates().reset_index(drop=True)
            )
            # newDF = self.keepWindowSize(newDataFrame)
            newDF = newDataFrame
            newDF.to_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDF.to_csv(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.csv"
            )

        else:
            newDF = self.keepWindowSize(df)
            newDF.to_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDF.to_csv(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/generatedDataFrame.csv"
            )
        if os.path.isfile(
            (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.pkl"
        ):
            prevInvocations = pd.read_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.pkl"
            )
            initRecords = df.loc[
                    (df["function"] == self.initFunc)
                ]
            initRecords = initRecords["start"]
            
            newInvocations = (
                pd.concat([prevInvocations, initRecords]).drop_duplicates().reset_index(drop=True)
            )
            print(newInvocations)
            newInvocations.to_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.pkl"
            )
            newInvocations.to_csv(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.csv"
            )

        else:
            initRecords = df.loc[
                    (df["function"] == self.initFunc)
                ]
            initRecords = initRecords["start"]
            print(initRecords)
            initRecords.to_pickle(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.pkl"
            )
            initRecords.to_csv(
                (os.path.dirname(os.path.abspath(__file__))) + "/data/" + self.workflow + "/invocationRates.csv"
            )

    def keepWindowSize(self, df):
        serverlessDF = df.loc[df["host"] == "s"]
        df.drop(
                df[
                    (df["host"] == "s")
                ].index,
                inplace=True,
            )
        df["start"] = pd.to_datetime(df["start"], utc=True)
        df.sort_values(by=["start"], ascending=False, inplace=True)
        vmSelectedDF = df.groupby(['host','function']).head(self.windowSize)
        finalDF = pd.concat([serverlessDF, vmSelectedDF]).drop_duplicates().reset_index(drop=True)
        return finalDF





if __name__ == "__main__":
    workflow = "Text2SpeechCensoringWorkflow"
    x = dataStoreLogParser(workflow)
