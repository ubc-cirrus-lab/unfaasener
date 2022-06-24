from datastoreGabageCollcetor import mergingDataGarbageCollector
from dataFrameGarbageCollector import garbageCollector
import time
import rankerConfig


class dataGarbageCollector:
    def __init__(self):
        workflow = rankerConfig.workflow
        serverless = mergingDataGarbageCollector()
        gc = garbageCollector(workflow)


if __name__ == "__main__":
    interuptTime = 60 * 60
    while True:
        start_time = time.time()
        x = dataGarbageCollector()
        print("--- %s seconds ---" % (time.time() - start_time))
        time.sleep(interuptTime)
