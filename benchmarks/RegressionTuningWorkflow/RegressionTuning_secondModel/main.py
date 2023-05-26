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
from sklearn import datasets
import time
import numpy as np
from io import StringIO
from random import choice
import tensorflow as tf
from tensorflow.keras import layers
import tarfile


batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
# Replace *** with your Google Cloud Project ID
PROJECT_ID = '***'
DSclient = datastore.Client()

def trainMain(event, context):
    routingData = (event['attributes'])['routing']
    routing = routingData[4]
    reqID = (event['attributes'])['reqID']
    dataset = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['dataset']
    message2send = train(dataset, reqID)
    # 0 for serverless, 1 for VM
    message_json = json.dumps({
      'data': {'dataset': message2send},
    })
    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == "0":
          topic_path = publisher.topic_path(PROJECT_ID, 'RegressionTuning_merged')
          publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], routing = routingData.encode("utf-8"), messageContent = "secondModel", branchName = "RegressionTuning", branch = "RegressionTuning_secondModel")
          publish_future.result()
    else:
        vmNumber = ord(routing) - 64
        vmTopic = "vmTopic"+ str(vmNumber)
        invokedFunction = "RegressionTuning_merged"
        topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
        publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'],invokedFunction = invokedFunction, routing = routingData.encode("utf-8"), messageContent = "secondModel", branchName = "RegressionTuning", branch = "RegressionTuning_secondModel")
        publish_future.result()

    logging.warning((event['attributes'])['reqID'])






def train(dataset, reqID):
    storage_client = storage.Client()
    bucket = storage_client.bucket("regression_tuning_storage")
    blob = bucket.blob(dataset)
    blob.download_to_filename("/tmp/"+dataset)
    with open("/tmp/"+dataset) as f:
        raw_data = f.readlines()
    # raw_data = StringIO("/tmp/"+dataset).readlines()
    dataset = [[float(_) for _ in d.strip().split('\t')] for d in raw_data]
    split_index = int(len(dataset) * 0.8)
    train_dataset = dataset[:split_index]
    test_dataset = dataset[split_index:]
    learning_rate = 0.2
    # build the model
    x_train = np.array([[_[0]] for _ in train_dataset])
    y_train = np.array([_[1] for _ in train_dataset])
    x_test = np.array([[_[0]] for _ in test_dataset])
    y_test = np.array([_[1] for _ in test_dataset])
    x_model = tf.keras.Sequential([
        layers.Dense(input_shape=[1,], units=1)
    ])
    x_model.compile(
        optimizer=tf.optimizers.Adam(learning_rate=learning_rate),
        loss='mean_absolute_error')
    history = x_model.fit(x_train, y_train,epochs=100, validation_split=0.2)
    hist = history.history
    # store loss for downstream tasks
    results = x_model.evaluate(x_test, y_test)
    model_name = "/tmp/"+"regression-Model"
    local_tar_name = "/tmp/"+str(reqID)+", model2.tar.gz"
    x_model.save(filepath=model_name)
    # zip keras folder to a single tar file
    with tarfile.open(local_tar_name, mode="w:gz") as _tar:
        _tar.add(model_name, recursive=True)
    upPath = str(reqID)+", model2.tar.gz"
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(local_tar_name)
    return upPath
