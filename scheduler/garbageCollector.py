from datastoreGarbageCollector import mergingDataGarbageCollector
from dataFrameGarbageCollector import garbageCollector
from vmDataFrameGC import VMgarbageCollector
from pathlib import Path
import time
import os

# import rankerConfig
import datetime
import configparser
import logging

logging.basicConfig(
    filename=str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/logs/GC.log",
    level=logging.INFO,
)


class dataGarbageCollector:
    def __init__(self):
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/rankerConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        workflow = self.rankerConfig["workflow"]
        serverless = mergingDataGarbageCollector()
        # gc = garbageCollector(workflow)
        # vmGC = VMgarbageCollector(workflow)


if __name__ == "__main__":
    interuptTime = 60 * 60
    time.sleep(interuptTime)
    while True:
        logging.info("GC is running......")
        logging.info(str(datetime.datetime.now()))
        start_time = time.time()
        x = dataGarbageCollector()
        print("--- %s seconds ---" % (time.time() - start_time))
        timeSpent = "time spent: " + str((time.time() - start_time))
        logging.info(timeSpent)
        time.sleep(interuptTime)
