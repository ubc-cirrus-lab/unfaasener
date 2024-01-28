from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query
from pathlib import Path
import os
import re
import numpy as np
import pandas as pd
import configparser


class monitoring:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path(os.path.dirname(os.path.abspath(__file__))))
            + "/key/monitoringKey.json"
        )
        configPath = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[0])
            + "/project-config.ini"
        )
        globalConfig = configparser.ConfigParser()
        globalConfig.read(configPath)
        self.projectConfig = globalConfig["settings"]
        project = str(self.projectConfig["projectid"])
        client = monitoring_v3.MetricServiceClient()
        q = query.Query(
            client, project, "pubsub.googleapis.com/topic/message_sizes", days=90
        )
        result = q.as_dataframe()

        topics = {}
        pubsubMeanMsgSize = {}
        for col in result.columns:
            topics[col[2]] = []
            for rec in range(len(result[col])):
                x = str(result[col].iloc[rec])
                if "mean" in x:
                    match = re.findall(r"mean: .+", x, flags=re.IGNORECASE)
                    mean = match[0].replace("mean:", "")
                    topics[col[2]].append(float(mean))
        for topic in topics:
            nptopic = np.array(topics[topic])
            pubsubMeanMsgSize[topic] = np.mean(nptopic)
        topic = []
        size = []

        for col in pubsubMeanMsgSize:
            topic.append(col)
            size.append(pubsubMeanMsgSize[col])
        dataframe = {"Topic": topic, "PubsubMsgSize": size}
        df = pd.DataFrame(dataframe)

        df.to_csv(
            (os.path.dirname(os.path.abspath(__file__))) + "/data/" + "topicMsgSize.csv"
        )
        df.to_pickle(
            (os.path.dirname(os.path.abspath(__file__))) + "/data/" + "topicMsgSize.pkl"
        )

        result.to_csv(
            (os.path.dirname(os.path.abspath(__file__))) + "/data/" + "pubsubsize.csv"
        )
