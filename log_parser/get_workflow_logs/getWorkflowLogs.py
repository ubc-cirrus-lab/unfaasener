from getNewServerlessLogs import getNewLogs
from getNewDatastoreLogs import dataStoreLogParser
import time
from pathlib import Path
import os
import sys
import logging
import datetime
logging.basicConfig(filename=str(Path(os.path.dirname(os.path.abspath(__file__))))+"/logs/logParser.log", level=logging.INFO)

class getWorkflowLogs():
    def __init__(self, workflow):
        serverless = getNewLogs(workflow)
        vm = dataStoreLogParser(workflow)


if __name__ == "__main__":
    interuptTime = 10*10
    initial = int(sys.argv[2])
    if initial == 1:
        start_time = time.time()
        # workflow = "Text2SpeechCensoringWorkflow"
        # workflow = "ChatBotWorkflow"
        workflow = sys.argv[1]
        x = getWorkflowLogs(workflow)
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print("---------getting new logs:---------------")
        time.sleep(interuptTime)
        while True:
                start_time = time.time()
                # workflow = "Text2SpeechCensoringWorkflow"
                # workflow = "ChatBotWorkflow"
                logging.info("periodic log parser is running......")
                logging.info(str(datetime.datetime.now()))
                workflow = sys.argv[1]
                x = getWorkflowLogs(workflow)
                print("--- %s seconds ---" % (time.time() - start_time))
                timeSpent = "time spent: " + str((time.time() - start_time))
                logging.info(timeSpent)
                time.sleep(interuptTime)