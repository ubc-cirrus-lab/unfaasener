import json
import boto3
import tarfile
from datetime import datetime
import os
import sys 
from io import StringIO
from random import choice
sys.path.append("/mnt/access")
import numpy as np
import tensorflow as tf
from tensorflow import keras

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    
    # Get input
    print("Join Runs Function")
    print(event)
    n_samples = json.loads(event[0]['body'])['data']['n_samples']
    reqID = json.loads(event[0]['body'])['data']['reqID']
    firstModel = json.loads(event[0]['body'])['data']['firstModel']
    secondModel = json.loads(event[1]['body'])['data']['secondModel']
    
    modelLists = []
    modelLists.append(firstModel)
    modelLists.append(secondModel)
    bestModel = choice(modelLists)
    
    bucket = s3.Bucket("regression-tuning-storage")
    
    bucket.download_file(bestModel, "/tmp/"+bestModel)
    zippedFile = tarfile.open("/tmp/"+bestModel)
    zippedFile.extractall("/tmp/Model")
    zippedFile.close()
    model = keras.models.load_model("/tmp/Model/tmp/regression-Model")
    
    inputModel = np.array([[0.57457947234]])
    # output is on the form {'predictions': [[10.879798]]}
    result = model.predict(inputModel)
    print(inputModel, result)
    assert result[0][0] > 0
    # assert result['predictions'][0][0] > 0
    os.remove("/tmp/"+bestModel)
    
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'bestModel': bestModel, 'reqID': reqID},
        })
    }

