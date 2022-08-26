from getNewServerlessLogs import getNewLogs
from getNewDatastoreLogs import dataStoreLogParser
import time
import sys

class getWorkflowLogs():
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
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print("---------getting new logs:---------------")
        while True:
                start_time = time.time()
                # workflow = "Text2SpeechCensoringWorkflow"
                # workflow = "ChatBotWorkflow"
                workflow = sys.argv[1]
                x = getWorkflowLogs(workflow)
                print("--- %s seconds ---" % (time.time() - start_time))
                time.sleep(interuptTime)