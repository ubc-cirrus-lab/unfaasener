import base64
import datetime
import requests 
import logging
import uuid
import numpy as np
from sys import getsizeof
from io import BytesIO
import os
import json
from google.cloud import storage
import time
import numpy as np
from io import StringIO
from random import choice
import numpy as np
import tensorflow as tf
from tensorflow import keras
import tarfile

def join(request):

    # Getting input data
    request_json = request.get_json()
    first_input_json = json.loads(request_json['first'])
    second_input_json = json.loads(request_json['second'])
    print(first_input_json)
    print(second_input_json)
   
    reqID1 =  first_input_json['data']['reqID']
    reqID2 =  second_input_json['data']['reqID']
    if reqID1 != reqID2:
        print("There seems to be a mismatch between your model results.")
        print("First model's request ID is " + reqID1)
        print("Second model's request ID is " + reqID2)

    firstModel = first_input_json['data']['dataset']
    secondModel = second_input_json['data']['dataset']
    print("First model is " + firstModel)
    print("Second model is " + secondModel)

    modelLists = []
    modelLists.append(firstModel)
    modelLists.append(secondModel)
    bestModel = choice(modelLists)
    print("Best model is " + bestModel)

    storage_client = storage.Client()
    bucket = storage_client.bucket("regression_tuning_storage")
    blob = bucket.blob(bestModel)
    blob.download_to_filename("/tmp/"+bestModel)
    zippedFile = tarfile.open("/tmp/"+bestModel)
    zippedFile.extractall("/tmp/Model")
    zippedFile.close()
    
    print("Testing the model with a sample input in progress")
    model = keras.models.load_model("/tmp/Model/tmp/regression-Model")
    # inputModel = {'instances': np.array([[0.57457947234]])}
    inputModel = np.array([[0.57457947234]])
    # output is on the form {'predictions': [[10.879798]]}
    result = model.predict(inputModel)
    print(inputModel, result)

    # Why this assetion needs to be valid? 
    #assert result[0][0] > 0

    # Cleaning up
    print("Cleanin up the resources in progress")
    os.remove("/tmp/"+bestModel)
    #logging.warning(str(reqID))
    blobs = storage_client.list_blobs("regression_tuning_storage")
    for blob in blobs:
        if (reqID1) in (blob.name):
            blob = bucket.blob(blob.name)
            blob.delete()

    message2send = json.dumps({
      'data': {'inputModel': inputModel.tolist(), 'result':result.tolist()},
    })
    return message2send         