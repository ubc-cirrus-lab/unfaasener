from google.cloud import datastore
from datetime import timedelta
import datetime
import os
from pathlib import Path
import datetime
import configparser


class mergingDataGarbageCollector:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path(os.path.dirname(os.path.abspath(__file__))))
            + "/key/schedulerKey.json"
        )
        configPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/project-config.ini"
        )
        globalConfig = configparser.ConfigParser()
        globalConfig.read(configPath)
        self.projectConfig = globalConfig["settings"]
        project = str(self.projectConfig["projectid"])
        self.datastore_client = datastore.Client()
        self.remove()

    def remove(self):
        query = self.datastore_client.query(kind="Merging")
        results = list(query.fetch())
        for res in results:
            # print(res.key.id_or_name)
            if (res["Date"].replace(tzinfo=None)) <= (
                datetime.datetime.utcnow() - timedelta(minutes=60 * 4)
            ):
                merge_key = self.datastore_client.key("Merging", res.key.id_or_name)
                self.datastore_client.delete(merge_key)
