import base64
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
from pydub import AudioSegment
import os


publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def convert(event, context):
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = routingData[4]
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    dlFile = open("/tmp/"+fileName, 'rb').read()
    input = BytesIO(dlFile)
    inputSize = len(input.getvalue())
    speech = AudioSegment.from_mp3(input)
    output = BytesIO()
    speech.export(output, format="wav")


    result =  output.getvalue()
    newFileName = str(uuid.uuid4())+"-"+(event['attributes'])['reqID']
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    os.remove("/tmp/"+newFileName)

    message2send = newFileName

    message_json = json.dumps({
      'data': {'message': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex
    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'Text2SpeechCensoringWorkflow_Compression')
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber)
      invokedFunction = "Text2SpeechCensoringWorkflow_Compression"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()

    logging.warning((event['attributes'])['reqID'])

