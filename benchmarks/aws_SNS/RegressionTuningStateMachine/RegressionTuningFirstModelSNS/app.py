import json
import boto3
from datetime import datetime
import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import tarfile

s3 = boto3.resource('s3')

def lambda_handler(event, context):

    # Get and validate input
    if event == {}:
        print("Error: Event is not provided")
        return
    else:
        msg = event['Records'][0]['Sns']['Message']
        body = (json.loads(msg))['body']
        data = (json.loads(body))['data']

        n_samples = data['n_samples']
        datasetPath = data['upPath']
        reqID = data['reqID']

    bucket = s3.Bucket("regression-tuning-storage")
    bucket.download_file(datasetPath, "/tmp/"+datasetPath)

    with open("/tmp/"+datasetPath) as f:
        raw_data = f.readlines()

    dataset = [[float(_) for _ in d.strip().split('\t')] for d in raw_data]
    split_index = int(len(dataset) * 0.8)
    train_dataset = dataset[:split_index]
    test_dataset = dataset[split_index:]
    learning_rate = 0.1

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
    local_tar_name = "/tmp/"+str(reqID)+"-model1.tar.gz"
    x_model.save(filepath=model_name)
    # zip keras folder to a single tar file
    with tarfile.open(local_tar_name, mode="w:gz") as _tar:
        _tar.add(model_name, recursive=True)

    upPath = str(reqID)+"-model1.tar.gz"
    bucket.upload_file(local_tar_name, upPath)


    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'firstModel': upPath, 'reqID': reqID},
        })
    })

    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:RegressionTuningMerge",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
    )

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }