import base64
from sklearn import datasets
import base64
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
import os
import json
from google.cloud import storage
from time import time

def create_artificial_dataset(request):
     # Getting input data
     request_json = request.get_json()
     input_json = json.loads(request_json['message'])
    
     n_samples = input_json['data']['samplesNum']
     reqID =  input_json['data']['reqID']

     storage_client = storage.Client()
     bucket = storage_client.bucket("regression_tuning_storage")
     x, y = datasets.make_regression(n_samples=n_samples,
                                    n_features=1,
                                    n_informative=1,
                                    n_targets=1,
                                    bias=3.0,
                                    noise=1.0)
    # just make sure data is in the right format, i.e. one feature
     assert x.shape[1] == 1
#     write to file, tab separated
     path = "/tmp/" + "dataset.txt"
     with open(path, "w") as _file:
          for _ in range(len(x)):
               _file.write("{}\t{}\n".format(x[_][0], y[_]))
     upPath = str(reqID)+"_dataset.txt"
     resblob = bucket.blob(upPath)
     resblob.upload_from_filename(path)
     os.remove(path)
     message2send = upPath
     message_json = json.dumps({
      'data': {'dataset': upPath, 'reqID' : reqID},
    })
     return message_json