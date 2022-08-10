from getNewServerlessLogs import getNewLogs
from getNewDatastoreLogs import dataStoreLogParser
import time

class getWorkflowLogs():
    def __init__(self, workflow):
        serverless = getNewLogs(workflow)
        vm = dataStoreLogParser(workflow)


if __name__ == "__main__":
    interuptTime = 60*10
    while True:
        start_time = time.time()
        # workflow = "Text2SpeechCensoringWorkflow"
        workflow = "ChatBotWorkflow"
        x = getWorkflowLogs(workflow)
        print("--- %s seconds ---" % (time.time() - start_time))
        time.sleep(interuptTime)