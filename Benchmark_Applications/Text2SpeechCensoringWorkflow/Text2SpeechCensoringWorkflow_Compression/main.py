import base64
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
from pydub import AudioSegment
from io import BytesIO
import os
import json
from google.cloud import storage


publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def compress(event, context):
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
    routing = int(routingData[4])
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['convertedFileName']
    indexes = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['indexes']
    # print("filename:{}".format(fileName))
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    dlFile = open("/tmp/"+fileName, 'rb').read()
    dlFile = BytesIO(dlFile)
        # find out length of file
    dlFile.seek(0, os.SEEK_END)
    file_length = dlFile.tell()
    #reset file
    dlFile.seek(0)
    # print("Inputfilesize: "+str(file_length))
    outputfile=BytesIO()
    speech = AudioSegment.from_wav(dlFile)
    speech = speech.set_frame_rate(5000)
    speech = speech.set_sample_width(1)
    speech.export(outputfile, format="wav")
    
    # print file lengths
    #print("Inputfilesize: "+str(file_length))
    # print("Outputfilesize: "+str(len(outputfile.getvalue())))
    
    result =  outputfile.getvalue()
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
    # 0 for serverless, 1 for VM
    if routing == 1:
      invokedFunction = "Text2SpeechCensoringWorkflow_Censor"
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-test-vm')
    else:
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-Censor')

    message_json = json.dumps({
      'data': {'newFile': message2send, 'indexes' : indexes},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == 1:
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message2send)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message2send)), routing = routingData.encode('utf-8'))
        publish_future.result()
    logging.warning(str(reqID))
    


