from datetime import datetime
import requests 
import base64
import uuid
import os
import json
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.contrib.hooks.gcs_hook import GoogleCloudStorageHook
from airflow.providers.google.common.utils import id_token_credentials as id_token_credential_utils
import google.auth.transport.requests
from google.auth.transport.requests import AuthorizedSession
import logging


def input_arg(**kwargs):
    try:
        mess = kwargs['dag_run'].conf["message"]
        print("Retrieved: "+str(mess))
        return mess
    except:
        print("Could not read input value. Defaulting to 'Hello World!'")
        return "Hello World!"


def text2speech(**kwargs):
    ti = kwargs['ti']
    data = {"message": ti.xcom_pull(task_ids="input")}

    url = "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/text2speech_raw"
    request = google.auth.transport.requests.Request()  #this is a request for obtaining the the credentials
    id_token_credentials = id_token_credential_utils.get_default_id_token_credentials(url, request=request) # If your cloud function url has query parameters, remove them before passing to the audience 
    resp = AuthorizedSession(id_token_credentials).post(url=url, json=data) # the authorized session object is used to access the Cloud Function

    #response = requests.post("https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/text2speech_raw", json=data)
    logging.info(resp.content)
    fileName = str(uuid.uuid4())
    with open(fileName, "wb") as outfile:
        outfile.write(resp.content)
    gcs = GoogleCloudStorageHook()
    gcs.upload("text2speech-workflow-storage", fileName, fileName, mime_type='application/octet-stream')

    os.remove(fileName)
    return fileName


def conversion(**kwargs):
    ti = kwargs['ti']
    fileName = ti.xcom_pull(task_ids="text2speech")
    gcs = GoogleCloudStorageHook()
    gcs.download("text2speech-workflow-storage", fileName, fileName)
    file = open(fileName, 'rb').read()

    url = "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/conversion_raw"
    request = google.auth.transport.requests.Request()  #this is a request for obtaining the the credentials
    id_token_credentials = id_token_credential_utils.get_default_id_token_credentials(url, request=request) # If your cloud function url has query parameters, remove them before passing to the audience 
    resp = AuthorizedSession(id_token_credentials).post(url=url, data=file) # the authorized session object is used to access the Cloud Function

    #response = requests.post("https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/conversion_raw", data=file)
    newFileName = str(uuid.uuid4())
    with open(newFileName, "wb") as outfile:
        outfile.write(resp.content)
    gcs.upload("text2speech-workflow-storage", newFileName, newFileName, mime_type='application/octet-stream')
    os.remove(newFileName)
    return newFileName


def profanity(**kwargs):
    ti = kwargs['ti']
    data = {"message": ti.xcom_pull(task_ids="input")}

    url = "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/Profanity-Detection-Raw"
    request = google.auth.transport.requests.Request()  #this is a request for obtaining the the credentials
    id_token_credentials = id_token_credential_utils.get_default_id_token_credentials(url, request=request) # If your cloud function url has query parameters, remove them before passing to the audience 
    resp = AuthorizedSession(id_token_credentials).post(url=url, json=data) # the authorized session object is used to access the Cloud Function
    
    #response = requests.post("https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/Profanity-Detection-Raw", json=data)
    return json.loads(resp.content)["indexes"]


def censor(**kwargs):
    ti = kwargs['ti']
    indexes = ti.xcom_pull(task_ids="profanity")
    fileName = ti.xcom_pull(task_ids="compression")
    gcs = GoogleCloudStorageHook()
    gcs.download("text2speech-workflow-storage", fileName, fileName)
    message = {"to_censor" : open(fileName, 'rb'), "indexes" : json.dumps(indexes)}

    url = "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/censor_raw"
    request = google.auth.transport.requests.Request()  #this is a request for obtaining the the credentials
    id_token_credentials = id_token_credential_utils.get_default_id_token_credentials(url, request=request) # If your cloud function url has query parameters, remove them before passing to the audience 
    resp = AuthorizedSession(id_token_credentials).post(url=url, files=message) # the authorized session object is used to access the Cloud Function

    #response = requests.post("https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/censor_raw", files=message)
    newFileName = str(uuid.uuid4())
    with open(newFileName, "wb") as outfile:
        outfile.write(resp.content)
    gcs.upload("text2speech-workflow-storage", newFileName, newFileName, mime_type='application/octet-stream')
    os.remove(newFileName)
    return newFileName


def compression(**kwargs):
    ti = kwargs['ti']
    fileName = ti.xcom_pull(task_ids="conversion")
    gcs = GoogleCloudStorageHook()
    gcs.download("text2speech-workflow-storage", fileName, fileName)
    file = {"to_compress" : open(fileName, 'rb')}

    url = "https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/compression_raw"
    request = google.auth.transport.requests.Request()  #this is a request for obtaining the the credentials
    id_token_credentials = id_token_credential_utils.get_default_id_token_credentials(url, request=request) # If your cloud function url has query parameters, remove them before passing to the audience 
    resp = AuthorizedSession(id_token_credentials).post(url=url, files=file) # the authorized session object is used to access the Cloud Function

    #response = requests.post("https://northamerica-northeast1-ubc-serverless-ghazal.cloudfunctions.net/compression_raw", files=file)
    newFileName = str(uuid.uuid4())
    with open(newFileName, "wb") as outfile:
        outfile.write(resp.content)
    gcs.upload("text2speech-workflow-storage", newFileName, newFileName, mime_type='application/octet-stream')
    os.remove(newFileName)
    return newFileName


def cleanup(**kwargs):
    ti = kwargs['ti']
    gcs = GoogleCloudStorageHook()
    fileName = ti.xcom_pull(task_ids="censor")
    gcs.delete("text2speech-workflow-storage", fileName)
    fileName = ti.xcom_pull(task_ids="compression")
    gcs.delete("text2speech-workflow-storage", fileName)
    fileName = ti.xcom_pull(task_ids="conversion")
    gcs.delete("text2speech-workflow-storage", fileName)
    fileName = ti.xcom_pull(task_ids="text2speech")
    gcs.delete("text2speech-workflow-storage", fileName)


dag = DAG('CompressFirst', description='Audio workflow',
          schedule_interval=None,
          start_date=datetime(2017, 2, 1),
          catchup=False)

censor = PythonOperator(task_id='censor', python_callable=censor, dag=dag, provide_context=True)
input_arg = PythonOperator(task_id='input', python_callable=input_arg, dag=dag, provide_context=True)
text2speech = PythonOperator(task_id='text2speech', python_callable=text2speech, dag=dag, provide_context=True)
conversion = PythonOperator(task_id='conversion', python_callable=conversion, dag=dag, provide_context=True)
profanity = PythonOperator(task_id='profanity', python_callable=profanity, dag=dag, provide_context=True)
compression = PythonOperator(task_id='compression', python_callable=compression, dag=dag, provide_context=True)
cleanup = PythonOperator(task_id='cleanup', python_callable=cleanup, dag=dag, provide_context=True)

input_arg >> [profanity, text2speech] >> conversion >> compression >> censor >> cleanup