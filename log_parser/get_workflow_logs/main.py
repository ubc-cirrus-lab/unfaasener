import subprocess
import json
import shlex
import datetime
from sys import getsizeof
import time
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import math
import pandas as pd
from generateData import generateData
from analyzeLogs import AnalyzeLogs
from getWorkflowLogs import GetWorkflowLogs

workflow = "ImageProcessingWorkflow"
# workflow = "Text2SpeechCensoringWorkflow"

with open(os.getcwd()+"/data/"+ workflow+ ".json", 'r') as json_file:
    workflow_json = json.load(json_file)

initFunc = workflow_json["initFunc"]
messages = workflow_json["messages"]
workflowFunctions = workflow_json["workflowFunctions"]
successors = workflow_json["successors"]
predecessors = workflow_json["predecessors"]

funcPaths = []

workflowObj = GetWorkflowLogs(workflow, messages,workflowFunctions, initFunc)
dataPath, publisheExeIDsPath, messageExePath = workflowObj.saveResults()

################################Just for testing a part of the logs analysis
# dataPath = "/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/ImageProcessingWorkflow/20, data.json"
# publisheExeIDsPath = "/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/ImageProcessingWorkflow/20, publisheExeIDs.json"
# messageExePath = "/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/ImageProcessingWorkflow/20, messageExe.json"

for func in workflowFunctions:
    if (len(predecessors[workflowFunctions.index(func)]) > 1):
        mergingPointFlag = True
    else:
        mergingPointFlag = False
    AnalyzeLogsObj = AnalyzeLogs(dataPath, publisheExeIDsPath, messageExePath, func, initFunc, workflow, mergingPointFlag)
    funcPath = AnalyzeLogsObj.getData()
    funcPaths = funcPaths+funcPath
    # funcPaths.append(funcPath)
print(funcPaths)
generateData(funcPaths, workflow, initFunc, workflowFunctions, successors)
workflow_json["dataframe"] = os.getcwd()+"/data/"+workflow +"/generatedData.pkl"
with open(os.getcwd()+"/data/"+ workflow+ ".json", 'w') as json_file:
    json.dump(workflow_json, json_file)
