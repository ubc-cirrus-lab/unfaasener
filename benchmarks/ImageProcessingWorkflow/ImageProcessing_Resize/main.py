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
from PIL import Image, ImageFilter
from time import time

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()


def resize(event, context):

    routingData = (event['attributes'])['routing']
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['imageName']
    storage_client = storage.Client()
    bucket = storage_client.bucket("imageprocessingworkflowstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    image = Image.open("/tmp/"+fileName)
    image.thumbnail((128, 128))
    path = "/tmp/" + "resized-" + fileName
    image.save(path)
    upPath = "resized-" + fileName
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(path)
    os.remove(path)
    os.remove("/tmp/"+fileName)
    garbage((event['attributes'])['reqID'])
    logging.warning((event['attributes'])['reqID'])



def garbage(reqID):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs("imageprocessingworkflowstorage")
    blobsNames = [blob.name for blob in blobs if reqID in blob.name ]
    bucket = storage_client.bucket("imageprocessingworkflowstorage")

    for blob in blobsNames:
        if not ((blob).startswith("Final")):
            deletedBlob = bucket.blob(blob)
            deletedBlob.delete()
