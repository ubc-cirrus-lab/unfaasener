import json
import base64
import json
import boto3
from datetime import datetime
import uuid
from MontagePy.main import *

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def lambda_handler(event, context):
    
    if event:
        # Getting input nd creating the reqID
        resolution = event['resolution']
        location = event['location']
        coordinate_system = event['coordinateSystem']
        size = event['size']
        fanout_num = event['fanoutNum']
        reqID = uuid.uuid4().hex
        
    if not resolution or not location or not coordinate_system or not size or not fanout_num:
        print(f'malformed request: {event}')
        exit(1)
        
    local_header_path = '/tmp/Montage.hdr'
    status = mHdr(location, size, size, local_header_path, resolution=resolution, csys=coordinate_system)
    perror(status)

    header_filename = f'header-{reqID}.hdr'
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('montagebenchmark')
    bucket.upload_file(local_header_path, header_filename)
    
    messages = []
    for color in ['red', 'blue', 'ir']:
        messages.append({
            'headerFileName': header_filename,
            'color': color,
            'fanoutNum': fanout_num,
            'reqID':reqID
        })
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'messages':messages},
        }
    }