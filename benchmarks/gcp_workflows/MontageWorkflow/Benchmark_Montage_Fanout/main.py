import base64
import json
from datetime import datetime
from sys import getsizeof
import uuid
import random
import numpy as np
from google.cloud import storage


def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def handler(request):
    
    request_json = request.get_json()
    req_id = request_json['reqID']
    header_file_name = request_json['headerFileName']
    color = request_json['color']
    fanout_num = request_json['fanoutNum']

    blobs = Montage_Project_Fanout(color)
    total_len = len(blobs)
    sizes = sizes_to_divide(total_len, fanout_num)

    messages = []
    cur = 0
    for i, size in enumerate(sizes):
        file_names = [blob.name for blob in blobs[cur:cur+size]]
        messages.append({
            'fitsFileNames': file_names,
            'headerFileName': header_file_name,
            'color': color,
            'index': i,
            'totalLen': total_len,
            'reqID': req_id
        })
        cur += size
        
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'messages':messages, 'reqID': req_id},
        }
    }
    
def Montage_Project_Fanout(color):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')
    li = list(bucket.list_blobs(prefix=f'data/{color}/'))
    return [f for f in li if f.name.endswith('.fits')]

def sizes_to_divide(total_len, fanout_num):
    base = total_len // fanout_num
    rest = total_len - base * fanout_num
    ret = []
    for i in range(fanout_num):
        ret.append(base + 1 if i < rest else base)
    return ret