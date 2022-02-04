import base64
from flask import escape
from google.cloud import datastore
import json
import datetime
import logging
import uuid
from sys import getsizeof
from google.cloud import pubsub_v1


publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'

def checking(event, context):
    datastore_client = datastore.Client()
    kind = "Merging"
    name = ( (event['attributes'])['branchName'] ) + ( (event['attributes'])['reqID'] )
    print(base64.b64decode(event['data']))
    reqID = ((event['attributes'])['reqID'])
    merge_key = datastore_client.key(kind, name)
    merge = datastore_client.get(key=merge_key)
    nextFunction = (merge["nextFunc"])
    newTotal = merge['numBranches']
    prevCounter = merge["Counter"]
    newCounter = prevCounter+1
    merge["Counter"] = newCounter
    resJson = (json.loads(merge["results"]))
    content = (event['attributes'])['messageContent']
    valueContent = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    newJson = {content : valueContent}
    print("event data:{}".format(base64.b64decode(event['data']).decode('utf-8')))
    resJson.update(newJson)
    merge["results"]= json.dumps(resJson)
    message = (json.loads(merge["results"]))
    if (newCounter == newTotal):
        print("all done!!")
        routingData = (event['attributes'])['routing']
        reqID = (event['attributes'])['reqID']
        routing = int((event['attributes'])['routingIndex'])
        message_json = json.dumps({
            'data': message,
        })
        message_bytes = message_json.encode('utf-8')
        msgID = uuid.uuid4().hex

        if routing == 1:
            invokedFunction = nextFunction
            topic_path = publisher.topic_path(PROJECT_ID, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), identifier = msgID, msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode("utf-8"))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(PROJECT_ID, nextFunction)
            publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), identifier = msgID, msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"))
            publish_future.result() 

        datastore_client.delete(merge_key)
    else:
        datastore_client.put(merge)
    print(f"Done")
    
  


