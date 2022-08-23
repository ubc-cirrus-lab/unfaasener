import sys
from pathlib import Path
import os
import json
# import rankerConfig
import configparser
import pandas as pd

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
        path = str(Path(os.path.dirname(os.path.abspath(__file__))))+"/rankerConfig.ini"
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        decisionModes = (self.rankerConfig["decisionMode"]).split()
        self.rankerConfig["workflow"] = workflow
        self.rankerConfig["mode"] = mode
        with open(path, "w") as configfile:
                self.config.write(configfile)
        for decisionMode in decisionModes:
            finalDecision = []
            for i in range(functionNum):
                eachFunc = [0] * int(vmNum)
                finalDecision.append(eachFunc)
            workflow_json[
                        "lastDecision" + "_" + decisionMode
                    ] = finalDecision
        with open(jsonPath, "w") as json_file:
            json.dump(workflow_json, json_file)
        dfPickel = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+workflow+"/generatedDataFrame.pkl"
                )
        dfCSV = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+workflow+"/generatedDataFrame.csv"
                )
        irPickel = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+workflow+"/invocationRates.pkl"
                )
        irCSV = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+workflow+"/invocationRates.csv"
                )
        dataJSONN = (
                    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
                    + "/log_parser/get_workflow_logs/data/"+workflow+"/data.json"
                )
        filePaths = [dfPickel, dfCSV, irPickel, irCSV, dataJSONN]
        for filePath in filePaths:
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