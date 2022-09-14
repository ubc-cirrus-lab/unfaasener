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
import sys
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def convert(event, context):
    event=json.loads(event)
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = routingData[3]
#    message = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    message = (event['data'])['data']['message']
    message2send = Text2SpeechCensoringWorkflow_Text2Speech(message, reqID)


    message_json = json.dumps({
      'data': {'message': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    # 0 for serverless, 1 for VM
    if routing == "0":
        topic_path = publisher.topic_path(PROJECT_ID, 'dag-Conversion')
        publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), routing = routingData.encode('utf-8'))
        publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber)
      invokedFunction = "Text2SpeechCensoringWorkflow_Conversion"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()

    logging.warning(str(reqID))

def Text2SpeechCensoringWorkflow_Text2Speech(message, reqID):
    tts = gTTS(text=message, lang='en')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    result = mp3_fp.getvalue()
    fileName = str(uuid.uuid4())+"-"+reqID
    with open("/tmp/"+fileName, "wb") as outfile:
        outfile.write(result)
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.upload_from_filename("/tmp/"+fileName)
    os.remove("/tmp/"+fileName)
    message2send = fileName
    return message2send

def main():
    convert(sys.argv[1],sys.argv[2])
if __name__ == '__main__':
    main()


