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

    # print("Inputfilesize: " + str(inputSize))
    # print("Outputfilesize: " + str(len(output.getvalue())))

    result =  output.getvalue()
    newFileName = str(uuid.uuid4())+"-"+(event['attributes'])['reqID']
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    # print(
    #     "File {} uploaded to {}.".format(
    #         "/tmp/"+newFileName, newFileName
    #     ))
    os.remove("/tmp/"+newFileName)

    message2send = newFileName
    topic_path = publisher.topic_path(PROJECT_ID, 'Merging')
    message_json = json.dumps({
      'data': {'message': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], msgSize = str(getsizeof(message2send)), routing = routingData.encode("utf-8"), messageContent = "convertedFileName", branchName = "Text2SpeechCensoringWorkflow_Compression", routingIndex = str(3))
    publish_future.result()
    logging.warning((event['attributes'])['reqID'])

