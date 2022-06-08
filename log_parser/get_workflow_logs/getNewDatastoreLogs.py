import time
import numpy as np
import os
import json
from pathlib import Path
from google.cloud import datastore
import pandas as pd
from getNewLogs import GetLog
import datetime


class dataStoreLogParser(GetLog):
    def __init__(self, workflow):
        super().__init__(workflow)
        jsonPath = (
            os.getcwd() +
            "/data/"
            + self.workflow
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        self.workflowFunctions = workflow_json["workflowFunctions"]
        self.dictData = {}
        self.windowSize = 50
        self.dictData["function"] = []
        self.dictData["reqID"] = []
        self.dictData["start"] = []
        self.dictData["finish"] = []
        self.dictData["mergingPoint"] = []
        self.dictData["host"] = []
        self.dictData["duration"] = []
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path(os.getcwd()).resolve().parents[1])
            + "/scheduler/key/schedulerKey.json"
        )
        project = "ubc-serverless-ghazal"
        self.datastore_client = datastore.Client()
        self.getNewLogs()
        self.saveNewLogs()

    def getNewLogs(self):

        query = self.datastore_client.query(kind="vmLogs")
        for func in self.workflowFunctions:
            query.add_filter("function", "=", func)
        results = list(query.fetch())
        for res in results:
            self.dictData["function"].append(res["function"])
            self.dictData["reqID"].append(res["reqID"])
            self.dictData["start"].append(res["start"])
            self.dictData["finish"].append(res["finish"])
            self.dictData["mergingPoint"].append(res["mergingPoint"])
            self.dictData["host"].append(res["host"])
            self.dictData["duration"].append(res["duration"])
            log_key = self.datastore_client.key("vmLogs", res.key.id_or_name)
            self.datastore_client.delete(log_key)

    def saveNewLogs(self):
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
            newDF = self.keepWindowSize(newDataFrame)
            newDF.to_pickle(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDF.to_csv(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.csv"
            )

        else:
            newDF = self.keepWindowSize(df)
            newDF.to_pickle(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.pkl"
            )
            newDF.to_csv(
                os.getcwd() + "/data/" + self.workflow + "/generatedDataFrame.csv"
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
