import base64
import json
from scipy.linalg import svd
import numpy
from numpy import array
import numpy as np
import logging
import uuid
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import datastore
import random
import time
import io
import datetime
from random import randint
from sys import getsizeof

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)

publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()
storage_client = storage.Client()
bucket = storage_client.bucket("chatbot_storagee")
# s3_client = boto3.client(
#  's3',
#  aws_access_key_id=accessKeyId,
#  aws_secret_access_key=accessKey
# )
# bucket_name = bucketName
# config = TransferConfig(use_threads=False)ac
 
def upload_matrix(A,  filename):
     numpy.savetxt("/tmp/"+filename, A)
     upPath = filename
     resblob = bucket.blob(upPath)
     resblob.upload_from_filename("/tmp/"+filename)
    #  s3_client.upload_file("/tmp/"+filename, bucket_name, "ChatBotData/" + filename, Config=config)

def upload_BOW(BOW):
    with open('/tmp/bos.txt','w') as f:
         for word in BOW:
             f.write(word+ '\n')
    f.close()
    resblob = bucket.blob('bos.txt')
    resblob.upload_from_filename('/tmp/bos.txt')    
    # s3_client.upload_file('/tmp/bos.txt', bucket_name, "ChatBotData/" + 'bos.txt', Config=config)
        
     
def main(fileName, event):
    eventt = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']
    Network_Bound = eventt["Network_Bound"]
    start_time = int(round(time.time() * 1000))
    data = []
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    with open("/tmp/"+fileName, 'r') as file:
         data = file.read().replace('\n', '')
    
    j_data = json.loads(data)    
    all_unique_words = []
    
    all_intents=[]
    for v in range(len(j_data["intents"])):
        newIntent = {}
        newIntent["name"] = j_data["intents"][v]["intent"]
        newIntent["data"] = j_data["intents"][v]["text"]
        newIntent["data"].extend(j_data["intents"][v]["responses"])
        for utterance in newIntent["data"]:
            words_list= utterance.split(" ") 
            all_unique_words.extend(words_list)
        all_intents.append(newIntent)
        #print(newIntent)
        # print("*************")
        #print("*************")
    BOW=set(all_unique_words)
    All_matrices=[]
    for newIntent in all_intents:
        # print(newIntent["name"])
        list_vectors=[]
        for utterance in  newIntent["data"]:
            words_list = utterance.split(" ")
            vector = [int(w in words_list) for w in BOW]
            #print(vector)
            list_vectors.append(vector)
        A = array(list_vectors)
        All_matrices.append(A)
    
    end_time = int(round(time.time() * 1000))
    # print("duration before upload:" + str(end_time-start_time))
    
    returnedDic={}
    returnedDic["detail"] = {}
    returnedDic["detail"]["indeces"] = []
    bundle_size = eventt["bundle_size"]
    list_of_inputs_to_bundle = []
    
    for mat_index in range(len(All_matrices)):
        positive_A = All_matrices[mat_index]
        negative_A = []
        if(mat_index > len(All_matrices) -4):
             
            negative_A =  All_matrices[0]
            negative_A = np.concatenate((negative_A, All_matrices[1]), axis=0)
            negative_A = np.concatenate((negative_A, All_matrices[2]), axis=0)
            
        else:
            negative_A =  All_matrices[mat_index+1]
            negative_A = np.concatenate((negative_A, All_matrices[mat_index+2]), axis=0)
            negative_A = np.concatenate((negative_A, All_matrices[mat_index+3]), axis=0)
            
        if(Network_Bound==1):    
            upload_matrix(positive_A, all_intents[mat_index]["name"] + "_pos.txt")
            upload_matrix(negative_A, all_intents[mat_index]["name"] + "_neg.txt")
            
        j={ "intent_name":all_intents[mat_index]["name"], "skew" : eventt["skew"], "Network_Bound" : eventt["Network_Bound"]}
        list_of_inputs_to_bundle.append(j)
        if(len(list_of_inputs_to_bundle) >= bundle_size):
            newDict = {}
            newDict["values"] = list_of_inputs_to_bundle
            end_time = int(round(time.time() * 1000))
            newDict["duration"] = end_time - start_time
            returnedDic["detail"]["indeces"].append(newDict)
            list_of_inputs_to_bundle = []
    
    upload_BOW(BOW)
    end_time = int(round(time.time() * 1000))
    if(len(list_of_inputs_to_bundle) > 0):
        newDict = {}
        newDict["values"] = list_of_inputs_to_bundle
        newDict["duration"] = end_time - start_time
        returnedDic["detail"]["indeces"].append(newDict)

    
    
    # return returnedDic
    # datastore_client = datastore.Client()
    # kind = "Merging"
    # name =  "ChatBot" + ( (event['attributes'])['reqID'] )
    # merge_key = datastore_client.key(kind, name)
    # merge = datastore_client.get(key=merge_key)
    # merge['numBranches'] = len(returnedDic["detail"]["indeces"])
    # datastore_client.put(merge)
    routingData = (event['attributes'])['routing']
    routing = routingData[2]
    # print("num of branches:::", (len(returnedDic["detail"]["indeces"])))
    for i in range(len(returnedDic["detail"]["indeces"])):
        message_json = json.dumps({
        'data': {'message': str(returnedDic["detail"]["indeces"][i])},
        })
        reqID = (event['attributes'])['reqID']
        message_bytes = message_json.encode('utf-8')
        msgID = uuid.uuid4().hex
        if routing == "0":
            topic_path = publisher.topic_path(PROJECT_ID, 'ChatBot_TrainIntent')
            publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            vmNumber = ord(firstRouting) - 64
            vmTopic = "vmTopic"+ str(vmNumber)
            invokedFunction = "ChatBot_TrainIntent"
            topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
            publish_future = publisher.publish(topic_path, data=message_bytes,reqID = (event['attributes'])['reqID'], publishTime = str(datetime.datetime.utcnow()), identifier = msgID, invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
    logging.warning((event['attributes'])['reqID'])
        
def handler(event, context):
    # if('dummy' in event) and (event['dummy'] == 1):
    #     print("Dummy call, doing nothing")
    #     return {"Message" : "Dummy call to Split Chatbot"}
        
    main("Intent.json", event) 
    # TODO implement
    #return {
    #    'statusCode': 200,
    #    'body': json.dumps('Hello from Lambda!')
    #}

