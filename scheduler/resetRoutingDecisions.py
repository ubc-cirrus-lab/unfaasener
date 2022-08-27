import time
import numpy as np
import sys
import os
import json
from pathlib import Path
from google.cloud import datastore
import sys
import copy
import datetime


class resetDicision:
    def __init__(self, workflow, vmNum):
        self.jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + ".json"
        )
        with open(self.jsonPath, "r") as json_file:
            self.workflow_json = json.load(json_file)
        self.functionNum = len(self.workflow_json["workflowFunctions"])
        self.workflow = workflow
        self.vmNum = vmNum
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(Path(os.path.dirname(os.path.abspath(__file__))))+"/key/schedulerKey.json"
        project = "ubc-serverless-ghazal"
        self.datastore_client = datastore.Client()
        kind = "routingDecision"
        name = self.workflow
        routing_key = self.datastore_client.key(kind, name)
        self.routing = self.datastore_client.get(key=routing_key)
        self.resetRouting()
        self.resetSavedTimestamps()


    def resetSavedTimestamps(self):
        now = str(datetime.datetime.now())
        dataJSONN = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+self.workflow+"/data.json"
                )
        newData = {}
        for func in self.workflow_json["workflowFunctions"]:
            newData[func] = now
        with open(dataJSONN, "w") as outfile:
            json.dump(newData, outfile)


    def resetRouting(self):
        rates = [25,50,75,95]
        for percent in rates:
            finalDecision = []
            for i in range(self.functionNum):
                eachFunc = [0] * int(self.vmNum)
                finalDecision.append(eachFunc)
            self.routing["routing" + "_" + str(percent)] = str(finalDecision)
        self.routing["active"] = "50"
        self.datastore_client.put(self.routing)


if __name__ == "__main__":
    workflow = sys.argv[1]
    vmNum = sys.argv[2]
    reset = resetDicision(workflow, vmNum)