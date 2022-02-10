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
initFunc = "ImageProcessing_GetInput"
messages = ["Final-test1.jpg", "Final-test2.jpg", "Final-test3.jpg", "Final-test4.jpg", "Final-test5.jpg", "Final-test6.jpg", "Final-test7.jpg", "Final-test8.jpg", "Final-test9.jpg", "Final-test10.jpg"]
workflowFunctions = ["ImageProcessing_GetInput", "ImagProcessing_Flip", "ImageProcessing_Rotate", "ImageProcessing_Filter", "ImageProcessing_Greyscale", "ImageProcessing_Resize"]
successors =[["ImagProcessing_Flip"], ["ImageProcessing_Rotate"], ["ImageProcessing_Filter"], ["ImageProcessing_Greyscale"], ["ImageProcessing_Resize"], []]

# workflowFunctions = ["Text2SpeechCensoringWorkflow_GetInput", "Text2SpeechCensoringWorkflow_Profanity", "Text2SpeechCensoringWorkflow_Text2Speech", "Text2SpeechCensoringWorkflow_Conversion", "Text2SpeechCensoringWorkflow_Compression", "Text2SpeechCensoringWorkflow_Censor"]
# workflow = "Text2SpeechCensoringWorkflow"
# initFunc = "Text2SpeechCensoringWorkflow_GetInput"
# messages= ["Ach it was hopeless. That was what ye felt. These bastards. What can ye do but. Except start again so he started again. That was what he did he started again … ye just plough on, ye plough on, ye just fucking plough on … ye just fucking push ahead, ye get fucking on with it", 
#          "They fuck you up, your mum and dad.They may not mean to, but they do. They fill you with the faults they hadAnd add some extra, just for you.",
#          "They can’t handle being in the same cities with the aliens, being on the same buses, shuttles and transport tubes. I mean, have you ever seen a Sklorno up close?” Stedmar’s face wrinkled with disgust",
#          "It was a large room with endless row of bottles upon tiers of shelves lining its walls. Several long tables stood about, and Tubby saw they were crowded with curious apparatus—little tubes in racks, microscopes, triangular pieces of glass with candles behind them, and several contrivances of wheels and weights that looked like clock works. In the exact center of the room was one larger apparatus of a sort Tubby had never seen before; it seemed very complicated and he stared at it with awe. He could make nothing out of it except that part of it was a huge telescope, extending up through the skylight of the room. He glanced upward, and there, through a narrow, open slit in the glass, he could see the stars shining",
#          "He switched off the lights. The room was quite dark except for a little beam of white light that seemed to thread its way through the intricate system of mirrors and prisms of the Light Machine. Tubby could not see where this light came from or where it went to. But he saw distinctly that it turned several corners and was alternately broad and narrow. It was white throughout most of its course; but in one short span it was a dark, angry red, and in another a deep, beautiful purple."]
# successors = [["Text2SpeechCensoringWorkflow_Profanity", "Text2SpeechCensoringWorkflow_Text2Speech"], ["Text2SpeechCensoringWorkflow_Compression"], ["Text2SpeechCensoringWorkflow_Conversion"], ["Text2SpeechCensoringWorkflow_Compression"], ["Text2SpeechCensoringWorkflow_Censor"], []]



funcPaths = []
workflowObj = GetWorkflowLogs(workflow, messages,workflowFunctions, initFunc)
dataPath, publisheExeIDsPath, messageExePath = workflowObj.saveResults()
for func in workflowFunctions:
    AnalyzeLogsObj = AnalyzeLogs(dataPath, publisheExeIDsPath, messageExePath, func, initFunc, workflow)
    funcPath = AnalyzeLogsObj.getData()
    funcPaths.append(funcPath)

generateData = generateData(funcPaths, workflow, initFunc, workflowFunctions, successors)

