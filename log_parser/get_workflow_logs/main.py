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

with open(os.getcwd()+"/data/"+ workflow+ ".json") as json_file:
    workflow_json = json.load(json_file)

initFunc = workflow_json["initFunc"]
messages = workflow_json["messages"]
workflowFunctions = workflow_json["workflowFunctions"]
successors = workflow_json["successors"]

funcPaths = []
workflowObj = GetWorkflowLogs(workflow, messages,workflowFunctions, initFunc)
dataPath, publisheExeIDsPath, messageExePath = workflowObj.saveResults()
for func in workflowFunctions:
    AnalyzeLogsObj = AnalyzeLogs(dataPath, publisheExeIDsPath, messageExePath, func, initFunc, workflow)
    funcPath = AnalyzeLogsObj.getData()
    funcPaths.append(funcPath)

generateData = generateData(funcPaths, workflow, initFunc, workflowFunctions, successors)

