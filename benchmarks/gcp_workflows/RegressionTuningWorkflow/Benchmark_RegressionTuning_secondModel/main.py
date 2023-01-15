import base64
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
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

def train(request):

    # Getting input
    request_json = request.get_json()
    input_json = json.loads(request_json['message'])

    print(input_json)
    
    dataset = input_json['data']['dataset']
    reqID =  input_json['data']['reqID']

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
    local_tar_name = "/tmp/"+str(reqID)+"_model2.tar.gz"
    x_model.save(filepath=model_name)
    # zip keras folder to a single tar file
    with tarfile.open(local_tar_name, mode="w:gz") as _tar:
        _tar.add(model_name, recursive=True)
    upPath = str(reqID)+"_model2.tar.gz"
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(local_tar_name)
    
    message2send = json.dumps({
      'data': {'dataset': upPath, 'reqID': reqID},
    })
    return message2send