from getNewServerlessLogs import getNewLogs
from getNewDatastoreLogs import dataStoreLogParser
import time
from pathlib import Path
import os
import sys
import logging
import datetime
import configparser


logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__))))
    + "/logs/logParser.log",
    level=logging.INFO,
)
sys.path.append(
    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
    + "/scheduler"
)
from baselineSlackAnalysis import baselineSlackAnalysis
from monitoring import monitoring


class getWorkflowLogs:
    def __init__(self, workflow):
        serverless = getNewLogs(workflow)
        vm = dataStoreLogParser(workflow)


if __name__ == "__main__":
    interuptTime = 60
    initial = int(sys.argv[2])
    if initial == 1:
        start_time = time.time()
        # workflow = "Text2SpeechCensoringWorkflow"
        # workflow = "ChatBotWorkflow"
        workflow = sys.argv[1]
        x = getWorkflowLogs(workflow)
        path = (
                str(
                    Path(os.path.dirname(os.path.abspath(__file__)))
                    .resolve()
                    .parents[1]
                )
                + "/scheduler/rankerConfig.ini"
            )
        config = configparser.ConfigParser()
        config.read(path)
        rankerConfig = config["settings"]
        mode = rankerConfig["mode"]
        if mode == "latency":
            baselineSlackAnalysis = baselineSlackAnalysis(workflow)
            # rankerConfig["tolerancewindow"] = str(2* (baselineSlackAnalysis.getCriticalPathDuration()))
        monitoringObj = monitoring()
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print("---------getting new logs:---------------")
        time.sleep(interuptTime)
        while True:
            start_time = time.time()
            workflow = sys.argv[1]
            # workflow = "Text2SpeechCensoringWorkflow"
            # workflow = "ChatBotWorkflow"
            logging.info("periodic log parser is running......")
            logging.info(str(datetime.datetime.now()))
            x = getWorkflowLogs(workflow)
            print("--- %s seconds ---" % (time.time() - start_time))
            timeSpent = "time spent: " + str((time.time() - start_time))
            logging.info(timeSpent)
            time.sleep(interuptTime)
