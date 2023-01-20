import subprocess
import json
import shlex
from sys import getsizeof
import time
import os
import math


class GetWorkflowLogs:
    def __init__(self, workflow, messages, functions, initFunc):
        self.count = 20
        self.sleepTime = 1
        self.initFunc = initFunc
        self.msgExeDic = {}
        self.workflow = workflow
        self.messages = messages
        self.functions = functions
        self.messagesize = {}
        self.timeDiff = []
        self.execodes = []
        self.allLogs = {}
        self.writeLogs = {}
        for func in self.functions:
            self.allLogs[func] = []
            self.writeLogs[func] = []
        self.subscriberExe = {}
        self.publisherFinishedTime = {}
        self.getLogPeriod = math.floor(1000 / (self.count * 4))
        self.finalWord = False
        self.execute()

    def execute(self):
        self.getLogCounter = 0
        for msg in self.messages:
            if msg == self.messages[-1]:
                self.finalWord = True

            self.getLogCounter += 1
            #             if i == self.count-1:
            #                 self.finalWord = True
            self.getLatency(msg)
        # self.saveResults()
        # print("Files are saved")

    def saveResults(self):
        publisheExeIDsPath = (
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + str(self.count)
            + ", publisheExeIDs.json"
        )
        messageExePath = (
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + str(self.count)
            + ", messageExe.json"
        )
        dataPath = (
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + str(self.count)
            + ", data.json"
        )
        with open(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + str(self.count)
            + ", publisheExeIDs.json",
            "w",
        ) as publisherExeID:
            json.dump(self.execodes, publisherExeID)
        with open(
            (os.path.dirname(os.path.abspath(__file__)))
            + "/data/"
            + str(self.workflow)
            + "/"
            + str(self.count)
            + ", messageExe.json",
            "w",
        ) as publisherExeID:
            json.dump(self.msgExeDic, publisherExeID)
        print("Files are saved")
        return dataPath, publisheExeIDsPath, messageExePath

    def getLatency(self, msg):

        self.callWorkflow(msg)
        if (self.getLogCounter == self.getLogPeriod) or (self.finalWord == True):
            self.getLogCounter = 0
            time.sleep(20)
            self.getLogs()
            if self.finalWord == True:
                print(
                    "Message "
                    + msg
                    + " with "
                    + str(getsizeof(msg))
                    + " bytes is called for "
                    + str(self.count)
                    + " times!"
                )

    def callWorkflow(self, msg):
        for c in range(self.count):
            res = subprocess.check_output(
                shlex.split(
                    'curl -X POST "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/'
                    + self.initFunc
                    + '"'
                    + ' --data \'{"message":"'
                    + (msg)
                    + '", "routing":"'
                    + "0000000000"
                    + '"}\' -H "Content-Type:application/json"'
                )
            )
            resString = res.decode("utf-8")
            exeId = resString
            print("-----------------" + str(c) + "-----------------")
            print("Execution ID: " + exeId)
            #             self.msgExeDic[exeId] = str(getsizeof(msg))
            self.msgExeDic[exeId] = msg
            self.execodes.append(exeId)
            time.sleep(self.sleepTime)
        print(
            "Workflow with Input: "
            + msg
            + " is triggered for "
            + str(self.count)
            + " times!"
        )

    def getLogs(self):
        for func in self.functions:
            project_list_logs = (
                "gcloud functions logs read "
                + func
                + " --region northamerica-northeast1 --format json --limit 1000"
            )
            project_logs = subprocess.check_output(shlex.split(project_list_logs))
            project_logs_json = json.loads(project_logs)
            (self.allLogs[func]).extend(project_logs_json)
        if self.finalWord == True:
            for func in self.functions:
                self.writeLogs[func] = self.allLogs[func]
            if os.path.isfile(
                (os.path.dirname(os.path.abspath(__file__)))
                + "/data/"
                + str(self.workflow)
                + "/"
                + str(self.count)
                + ", data.json"
            ):
                with open(
                    (os.path.dirname(os.path.abspath(__file__)))
                    + "/data/"
                    + str(self.workflow)
                    + "/"
                    + str(self.count)
                    + ", data.json",
                    "a",
                ) as outfile:
                    json.dump(self.writeLogs, outfile)
            else:
                with open(
                    (os.path.dirname(os.path.abspath(__file__)))
                    + "/data/"
                    + str(self.workflow)
                    + "/"
                    + str(self.count)
                    + ", data.json",
                    "w",
                ) as outfile:
                    json.dump(self.writeLogs, outfile)


if __name__ == "__main__":
    # workflow = "ImageProcessingWorkflow"
    # workflow = "Text2SpeechCensoringWorkflow"
    workflow = "ChatBotWorkflow"

    with open(
        (os.path.dirname(os.path.abspath(__file__))) + "/data/" + workflow + ".json",
        "r",
    ) as json_file:
        workflow_json = json.load(json_file)

    initFunc = workflow_json["initFunc"]
    messages = workflow_json["messages"]
    workflowFunctions = workflow_json["workflowFunctions"]
    successors = workflow_json["successors"]
    predecessors = workflow_json["predecessors"]

    workflowObj = GetWorkflowLogs(workflow, messages, workflowFunctions, initFunc)
