import json
from datetime import datetime
import boto3
import tempfile
import sys 
import os 
import cv2
import pickle

EXT = '.jpg'

class VideoDecoder:
    def __init__(self, filename, req_id, fanout_num):
        self.s3 = boto3.resource('s3')
        self.filename = filename
        self.bucket = self.s3.Bucket('videoanalyticsbenchmark')
        self.bucket_name = 'videoanalyticsbenchmark'
        # self.video_blob = self.bucket.blob(filename)
        self.req_id = req_id
        self.fanout_num = fanout_num

    def decode(self):
        obj = self.s3.Object(bucket_name=self.bucket_name, key=self.filename)
        response = obj.get()
        video_bytes = response['Body'].read()
        
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
        # print(f"filename is {filename}")
        # storage.put(filename, frame_bytes)
        # pickled = pickle.dumps(frame_bytes)
        s3object = self.s3.Object(bucket_name=self.bucket_name, key=filename)
        s3object.put(Body=frame_bytes)
        return filename

def lambda_handler(event, context):
    
    if event == {}:
        video_name = 'sample.mp4'
    else:
        video_name = json.loads(event['body'])['data']['videoName']
        fanout_num = json.loads(event['body'])['data']['fanoutNum'] 
        req_id = json.loads(event['body'])['data']['reqID']
        
        filenames = VideoAnalytics_Decoder(video_name, req_id, fanout_num)
        image_names_list = []
        
        for i in filenames:
            image_names_list.append({"imageName":i, "reqID":req_id})
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'videoName': video_name, 'reqID': req_id, 'fanoutNum': fanout_num, 'filenames': image_names_list},
        }
    }
    
def VideoAnalytics_Decoder(filename, req_id, fanout_num):
    decoder = VideoDecoder(filename, req_id, fanout_num)
    frames = decoder.decode()
    return [decoder.upload(i, frame) for i, frame in enumerate(frames)]
