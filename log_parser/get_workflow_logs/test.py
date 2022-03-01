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


# workflow = "ImageProcessingWorkflow"
workflow = "Text2SpeechCensoringWorkflow"

with open(os.getcwd()+"/data/"+ workflow+ ".json", 'r') as json_file:
    workflow_json = json.load(json_file)

initFunc = workflow_json["initFunc"]
messages = workflow_json["messages"]
workflowFunctions = workflow_json["workflowFunctions"]
successors = workflow_json["successors"]
predecessors = workflow_json["predecessors"]




funcPaths = ['/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_GetInput, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_Profanity, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_Text2Speech, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_Conversion, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_Compression, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_MergedFunction*Text2SpeechCensoringWorkflow_Compression, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_MergedFunction*Text2SpeechCensoringWorkflow_Profanity, data.json', '/Users/ghazal/Desktop/UBC/Research/de-serverlessization/log_parser/get_workflow_logs/data/Text2SpeechCensoringWorkflow/Text2SpeechCensoringWorkflow_Censor, data.json']
generateData(funcPaths, workflow, initFunc, workflowFunctions, successors)
dataframe = pd.read_pickle(os.getcwd()+"/data/"+workflow +"/generatedData.pkl")
# print(dataframe)