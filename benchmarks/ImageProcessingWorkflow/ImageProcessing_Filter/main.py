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


def filterr(event, context):
    routingData = (event['attributes'])['routing']
    routing = routingData[4]
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['imageName']
    message2send = ImageProcessing_Filter(fileName)
    # 0 for serverless, 1 for VM
    message_json = json.dumps({
      'data': {'imageName': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == "0":
        topic_path = publisher.topic_path(PROJECT_ID, 'ImageProcessing_Greyscale')
        publish_future = publisher.publish(topic_path, data=message_bytes, reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), routing = routingData.encode('utf-8'))
        publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber) 
      invokedFunction = "ImageProcessing_Greyscale"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(message2send)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()
    logging.warning((event['attributes'])['reqID'])



def ImageProcessing_Filter(fileName):
    storage_client = storage.Client()
    bucket = storage_client.bucket("imageprocessingworkflowstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    image = Image.open("/tmp/"+fileName)
    img = image.filter(ImageFilter.BLUR)
    path = "/tmp/" + "blur-" + fileName
    img.save(path)
    upPath = "blur-" + fileName
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(path)
    os.remove(path)
    os.remove("/tmp/"+fileName)
    message2send = upPath
    return message2send
