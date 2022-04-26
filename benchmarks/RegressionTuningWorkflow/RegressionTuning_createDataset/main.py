import base64
from sklearn import datasets
import base64
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
import os
import json
from google.cloud import storage
from time import time

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def create(event, context):
     routingData = (event['attributes'])['routing']
     firstRouting = routingData[2]
     secondRouting = routingData[3]
     reqID = (event['attributes'])['reqID']
     samplesNum = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['samplesNum']
     samplesNum = int(samplesNum)
     message2send = create_artificial_dataset(n_samples = samplesNum, reqID = reqID)
    # 0 for serverless, 1 for VM
     message_json = json.dumps({
      'data': {'dataset': message2send},
      })
     message_bytes = message_json.encode('utf-8')
     msgID = uuid.uuid4().hex

     if firstRouting == "0":
          topic_path = publisher.topic_path(PROJECT_ID, 'RegressionTuning_firstModel')
          publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), routing = routingData.encode('utf-8'))
          publish_future.result()
     else:
          vmNumber = ord(firstRouting) - 64
          vmTopic = "vmTopic"+ str(vmNumber)
          invokedFunction = "RegressionTuning_firstModel"
          topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
          publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
          publish_future.result()
     

     if secondRouting == "0":
          topic_path = publisher.topic_path(PROJECT_ID, 'RegressionTuning_secondModel')
          publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), routing = routingData.encode('utf-8'))
          publish_future.result()
     else:
          vmNumber = ord(secondRouting) - 64
          vmTopic = "vmTopic"+ str(vmNumber)
          invokedFunction = "RegressionTuning_secondModel"
          topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
          publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
          publish_future.result()

     logging.warning((event['attributes'])['reqID'])


def create_artificial_dataset(n_samples, reqID):
     storage_client = storage.Client()
     bucket = storage_client.bucket("regression_tuning_storage")
     x, y = datasets.make_regression(n_samples=n_samples,
                                    n_features=1,
                                    n_informative=1,
                                    n_targets=1,
                                    bias=3.0,
                                    noise=1.0)
    # just make sure data is in the right format, i.e. one feature
     assert x.shape[1] == 1
#     write to file, tab separated
     path = "/tmp/" + "dataset.txt"
     with open(path, "w") as _file:
          for _ in range(len(x)):
               _file.write("{}\t{}\n".format(x[_][0], y[_]))
     upPath = str(reqID)+", dataset.txt"
     resblob = bucket.blob(upPath)
     resblob.upload_from_filename(path)
     os.remove(path)
     message2send = upPath
     return message2send
