import base64
import datetime
import requests 
import logging
import uuid
import numpy as np
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
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

publisher = pubsub_v1.PublisherClient()
PROJECT_ID = '***'
DSclient = datastore.Client()

def join(event, context):
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
#     routing = int(routingData[4])
    firstModel = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['firstModel']
    secondModel = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['secondModel']
    modelLists = []
    modelLists.append(firstModel)
    modelLists.append(secondModel)
    bestModel = choice(modelLists)
    storage_client = storage.Client()
    bucket = storage_client.bucket("regression_tuning_storage")
    blob = bucket.blob(bestModel)
    blob.download_to_filename("/tmp/"+bestModel)
    zippedFile = tarfile.open("/tmp/"+bestModel)
    zippedFile.extractall("/tmp/Model")
    zippedFile.close()
    model = keras.models.load_model("/tmp/Model/tmp/regression-Model")
    # inputModel = {'instances': np.array([[0.57457947234]])}
    inputModel = np.array([[0.57457947234]])
    # output is on the form {'predictions': [[10.879798]]}
    result = model.predict(inputModel)
    print(inputModel, result)
    assert result[0][0] > 0
    # assert result['predictions'][0][0] > 0
    os.remove("/tmp/"+bestModel)
    logging.warning(str(reqID))
    blobs = storage_client.list_blobs("regression_tuning_storage")
    for blob in blobs:
        if (reqID) in (blob.name):
            blob = bucket.blob(blob.name)
            blob.delete()


