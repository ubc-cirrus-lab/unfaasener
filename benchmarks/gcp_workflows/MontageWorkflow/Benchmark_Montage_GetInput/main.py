import json
from datetime import datetime
from sys import getsizeof
import uuid
import random
from google.cloud import storage
from MontagePy.main import *

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

"""
Sample input json
{
    "resolution": 1.0,
    "size": 2,
    "coordinateSystem": "Equatorial",
    "location": "M31",
    "fanoutNum": 4
}
"""
def handler(request):
    
    # First Branch
    reqID = uuid.uuid4().hex

    request_json = request.get_json()
    resolution = request_json['resolution']
    location = request_json['location']
    coordinate_system = request_json['coordinateSystem']
    size = request_json['size']
    fanout_num = request_json['fanoutNum']

    if not resolution or not location or not coordinate_system or not size or not fanout_num:
        print(f'malformed request json: {request_json}')
        exit(1)

    local_header_path = '/tmp/Montage.hdr'
    status = mHdr(location, size, size, local_header_path, resolution=resolution, csys=coordinate_system)
    perror(status)

    header_filename = f'header-{reqID}.hdr'
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')
    blob = bucket.blob(header_filename)
    blob.upload_from_filename(local_header_path)

    
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