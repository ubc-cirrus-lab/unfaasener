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
# Replace *** with your Google Cloud Project ID
PROJECT_ID = '***'

def checking(event, context):
    datastore_client = datastore.Client()
    kind = "Merging"
    name = ( (event['attributes'])['branchName'] ) + ( (event['attributes'])['reqID'] )
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
    resJson.update(newJson)
    merge["results"]= json.dumps(resJson)
    message = (json.loads(merge["results"]))
    if (newCounter == newTotal):
        routingData = (event['attributes'])['routing']
        reqID = (event['attributes'])['reqID']
        routing = routingData[6]
        message_json = json.dumps({
            'data': message,
        })
        message_bytes = message_json.encode('utf-8')
        msgID = uuid.uuid4().hex

        if routing == "0":
            topic_path = publisher.topic_path(PROJECT_ID, "dag-Censor")
            publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), identifier = msgID, msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"))
            publish_future.result() 
        else:
            vmNumber = ord(routing) - 64
            vmTopic = "vmTopic"+ str(vmNumber) 
            invokedFunction = nextFunction
            topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
            publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), identifier = msgID, msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode("utf-8"))
            publish_future.result()


        datastore_client.delete(merge_key)
        
    else:
        datastore_client.put(merge)

    logging.warning((event['attributes'])['reqID'] +"*"+(event['attributes'])['branch'] )
    
  


