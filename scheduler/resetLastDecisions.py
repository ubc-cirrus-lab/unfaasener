import sys
from pathlib import Path
import os
import json

# import rankerConfig
import configparser
import datetime


class resetLastDicision:
    def __init__(self, workflow, vmNum, mode):
        workflow = workflow
        vmNum = vmNum
        mode = mode
        jsonPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + ".json"
        )
        with open(jsonPath, "r") as json_file:
            workflow_json = json.load(json_file)
        functionNum = len(workflow_json["workflowFunctions"])
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        decisionModes = (self.rankerConfig["decisionMode"]).split()
        self.rankerConfig["workflow"] = workflow
        self.rankerConfig["mode"] = mode
        self.rankerConfig["mufactor"] = str(1)
        self.rankerConfig["starttest"] = str(datetime.datetime.now())
        with open(path, "w") as configfile:
            self.config.write(configfile)
        for decisionMode in decisionModes:
            finalDecision = []
            for i in range(functionNum):
                eachFunc = [0] * int(vmNum)
                finalDecision.append(eachFunc)
            workflow_json["lastDecision" + "_" + decisionMode] = finalDecision
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        # reset datastore costs
        # prevDecisionPath = (
        #     str(Path(os.path.dirname(os.path.abspath(__file__))))+"/data/"
        #     + "prevCost.json"
        # )
        # with open(prevDecisionPath, "r") as json_file:
        #     prevCost_json = json.load(json_file)
        # prevCost_json["DSread"] = 0
        # prevCost_json["DSwrite"] = 0
        # prevCost_json["DSdelete"] = 0
        # with open(prevDecisionPath, "w") as json_file:
        #     json.dump(prevCost_json, json_file)
        pathDF = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/"
        )
        dfDir = Path(pathDF)
        dfFilesNames = [
            file.name
            for file in dfDir.iterdir()
            if ((file.name.startswith("generatedDataFrame")))
        ]
        invocationFilesNames = [
            file.name
            for file in dfDir.iterdir()
            if ((file.name.startswith("invocationRates")))
        ]
        irPaths = []
        dfPaths = []
        for dfName in dfFilesNames:
            dfPaths.append(pathDF + dfName)
        for irName in invocationFilesNames:
            irPaths.append(pathDF + irName)
        dfPickel = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/generatedDataFrame.pkl"
        )
        dfCSV = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/generatedDataFrame.csv"
        )
        irPickel = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/invocationRates.pkl"
        )
        irCSV = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/invocationRates.csv"
        )
        lockFile = str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/lock.txt"
        vmAgentLogFile = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/execution-agent/output2.log"
        )
        dateDataframepkl = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/dateDate.pkl"
        )
        dateDataframecsv = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/dateDate.csv"
        )
        prevDataJson = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/log_parser/get_workflow_logs/data/"
            + workflow
            + "/prevData.json"
        )
        triggersFile = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/monitoring-agent/triggers.txt"
        )
        utilFilePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/monitoring-agent/utilFile.txt"
        )
        forcedLockFile = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/forcedLock.txt"
        )
        VMcachDataframe = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/execution-agent/data/cachedVMData.csv"
        )

        # dataJSONN = (
        #             str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
        #             + "/log_parser/get_workflow_logs/data/"+workflow+"/data.json"
        #         )
        cachePath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/host-agents/execution-agent/data/cachedVMData.json"
        )
        filePaths = [
            dfPickel,
            dfCSV,
            irPickel,
            irCSV,
            lockFile,
            vmAgentLogFile,
            dateDataframepkl,
            dateDataframecsv,
            prevDataJson,
            cachePath,
            triggersFile,
            utilFilePath,
            forcedLockFile,
            VMcachDataframe,
        ]
        finalPaths = filePaths + dfPaths + irPaths
        for filePath in finalPaths:
            if os.path.isfile(filePath):
                os.remove(filePath)
                print(filePath, "has been deleted")
            else:
                print(filePath, "does not exist")


# print(initFunc)
# sys.exit(0)


if __name__ == "__main__":
    workflow = sys.argv[1]
    vmNum = int(sys.argv[2])
    mode = sys.argv[3]
    reset = resetLastDicision(workflow, vmNum, mode)
