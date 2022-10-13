import base64
import datetime
import json
import logging
import os
from sys import getsizeof
import uuid
import cv2
from google.cloud import storage

def streaming(request):
    request_json = request.get_json()
    filename = json.loads(request_json['message'])['body']['data']['videoName']
    fanout_num = json.loads(request_json['message'])['body']['data']['fanoutNum']
    req_id = json.loads(request_json['message'])['body']['data']['reqID']

    video_name = VideoAnalytics_Streaming(filename, req_id)

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'videoName': video_name, 'fanoutNum':fanout_num ,'reqID': req_id},
        }
    })

# This function resized the specified video.
def VideoAnalytics_Streaming(filename, req_id):
    local_filename = f'/tmp/{filename}'

    cli = storage.Client()
    src_bucket = cli.bucket('videoanalyticsworkflow-storage-src')
    src_blob = src_bucket.blob(filename)
    src_blob.download_to_filename(local_filename)

    resized_local_filename = resize_and_store(local_filename)

    dst_bucket = cli.bucket('videoanalyticsworkflow-storage')
    streaming_filename = f'{req_id}-{filename}'
    dst_blob = dst_bucket.blob(streaming_filename)
    dst_blob.upload_from_filename(resized_local_filename)

    os.remove(local_filename)
    os.remove(resized_local_filename)
    return streaming_filename

def resize_and_store(local_filename):
    cap = cv2.VideoCapture(local_filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    resized_local_filename = '/tmp/resized_video.mp4'
    width, height = 340, 256
    writer = cv2.VideoWriter(resized_local_filename, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (width, height))
        writer.write(frame)
    return resized_local_filename