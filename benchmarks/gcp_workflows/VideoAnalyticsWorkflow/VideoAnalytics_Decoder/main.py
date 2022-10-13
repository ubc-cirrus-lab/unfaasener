import base64
import datetime
import json
import logging
import os
from sys import getsizeof
import tempfile
import uuid
import cv2
from google.cloud import storage

EXT = '.jpg'

class VideoDecoder:
    def __init__(self, filename, req_id, fanout_num):
        client = storage.Client()
        self.bucket = client.bucket('videoanalyticsworkflow-storage')
        self.video_blob = self.bucket.blob(filename)
        self.req_id = req_id
        self.fanout_num = fanout_num

    def decode(self):
        video_bytes = self.video_blob.download_as_bytes()
        tmp = tempfile.NamedTemporaryFile(suffix='.mp4')
        tmp.write(video_bytes)
        tmp.seek(0)
        vidcap = cv2.VideoCapture(tmp.name)
        frames = []
        for i in range(self.fanout_num):
            _, image = vidcap.read()
            frames.append(cv2.imencode(EXT, image)[1].tobytes())
        return frames

    def upload(self, i, frame_bytes):
        filename = f'{self.req_id}-{i}{EXT}'
        blob = self.bucket.blob(filename)
        blob.upload_from_string(frame_bytes)
        return filename


def decode(request):
    request_json = request.get_json()

    video_name = json.loads(request_json['message'])['body']['data']['videoName']
    fanout_num = json.loads(request_json['message'])['body']['data']['fanoutNum']
    req_id = json.loads(request_json['message'])['body']['data']['reqID']

    filenames = VideoAnalytics_Decoder(video_name, req_id, fanout_num)
    
    return {
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'imageNames': filenames, 'reqID': req_id},
        }
    }


def VideoAnalytics_Decoder(filename, req_id, fanout_num):
    decoder = VideoDecoder(filename, req_id, fanout_num)
    frames = decoder.decode()
    return [decoder.upload(i, frame) for i, frame in enumerate(frames)]