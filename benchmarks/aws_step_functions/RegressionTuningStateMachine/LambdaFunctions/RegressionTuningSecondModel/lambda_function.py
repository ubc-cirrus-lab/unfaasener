import json
import boto3
from datetime import datetime
import os
import sys 
sys.path.append("/mnt/access")
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import tarfile

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    
    # Get input
    print("SecondModelTrain Function")
    print(event)
    n_samples = json.loads(event['body'])['data']['n_samples']
    datasetPath = json.loads(event['body'])['data']['upPath']
    reqID = json.loads(event['body'])['data']['reqID']
    
    bucket = s3.Bucket("regression-tuning-storage")
    bucket.download_file(datasetPath, "/tmp/"+datasetPath)
    
    with open("/tmp/"+datasetPath) as f:
        raw_data = f.readlines()
    
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
    local_tar_name = "/tmp/"+str(reqID)+"-model2.tar.gz"
    x_model.save(filepath=model_name)
    # zip keras folder to a single tar file
    with tarfile.open(local_tar_name, mode="w:gz") as _tar:
        _tar.add(model_name, recursive=True)
    
    upPath = str(reqID)+"-model2.tar.gz"
    bucket.upload_file(local_tar_name, upPath)
    
    
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'secondModel': upPath, 'reqID': reqID},
        })
    }

