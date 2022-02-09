import base64
from gtts import gTTS
from io import BytesIO
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

publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def convert(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """



    # print("messageSize:{}".format((event['attributes'])['msgSize']))
    # print("publishedTime:{},identifier:{},messageSize:{}".format((event['attributes'])['publishTime'], (event['attributes'])['identifier'], (event['attributes'])['msgSize']))
    # print(base64.b64decode(event['data']).decode('utf-8'))
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = int(routingData[2])
    message = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    tts = gTTS(text=message, lang='en')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    result = mp3_fp.getvalue()
        
    # print("MessageSize:" + str(len(message)))
    # print("FileSize:" + str(len(result)))
    fileName = str(uuid.uuid4())+"-"+(event['attributes'])['reqID']
    with open("/tmp/"+fileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.upload_from_filename("/tmp/"+fileName)
    # print(
    #     "File {} uploaded to {}.".format(
    #         "/tmp/"+fileName, fileName
    #     ))
    os.remove("/tmp/"+fileName)

    message2send = fileName

    # 0 for serverless, 1 for VM
    if routing == 1:
      invokedFunction = "Text2SpeechCensoringWorkflow_Conversion"
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-test-vm')
    else:
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-Conversion')

    message_json = json.dumps({
      'data': {'message': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == 1:
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), routing = routingData.encode('utf-8'))
        publish_future.result()
    logging.warning(str(reqID))
