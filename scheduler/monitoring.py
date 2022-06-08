from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query
import os
import re
import numpy as np
import pandas as pd


class monitoring:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key/monitoringKey.json"
        project = "ubc-serverless-ghazal"
        client = monitoring_v3.MetricServiceClient()
        q = query.Query(
            client, project, "pubsub.googleapis.com/topic/message_sizes", days=90
        )
        result = q.as_dataframe()

        topics = {}
        pubsubMeanMsgSize = {}
        for col in result.columns:
            topics[col[2]] = []
            # print(col[2])
            for rec in range(len(result[col])):
                # if "mean" in result[col][rec]:
                x = str(result[col][rec])
                if "mean" in x:
                    match = re.findall(r"mean: .+", x, flags=re.IGNORECASE)
                    mean = match[0].replace("mean:", "")
                    topics[col[2]].append(float(mean))
            # print(result[col][1])
        for topic in topics:
            nptopic = np.array(topics[topic])
            pubsubMeanMsgSize[topic] = np.mean(nptopic)
        print(pubsubMeanMsgSize)
        topic = []
        size = []

        for col in pubsubMeanMsgSize:
            topic.append(col)
            size.append(pubsubMeanMsgSize[col])
        dataframe = {"Topic": topic, "PubsubMsgSize": size}
        df = pd.DataFrame(dataframe)

        df.to_csv(os.getcwd() + "/data/" + "topicMsgSize.csv")
        df.to_pickle(os.getcwd() + "/data/" + "topicMsgSize.pkl")

        result.to_csv(os.getcwd() + "/data/" + "pubsubsize.csv")
