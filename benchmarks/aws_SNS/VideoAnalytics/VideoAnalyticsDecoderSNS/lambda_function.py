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
def lambda_handler(event, context):
    
    if event == {}:
        video_name = 'sample.mp4'
    else:
        msg = event['Records'][0]['Sns']['Message']
        body = (json.loads(msg))['body']
        data = (json.loads(body))['data']
        
        video_name = data['videoName']
        fanout_num = data['fanoutNum']
        req_id = data['reqID']
        
        filenames = VideoAnalytics_Decoder(video_name, req_id, fanout_num)
        response = {}
        client = boto3.client('sns')
        
        for i, filename in enumerate(filenames):
            notification = json.dumps({'data': {'imageName': filename, 'reqID': req_id}})
            response = client.publish (
                TargetArn = "arn:aws:sns:us-east-2:417140135939:VideoAnalytics_Recognition",
                Message = json.dumps({'default': notification}),
                MessageStructure = 'json'
           )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }
    
def VideoAnalytics_Decoder(filename, req_id, fanout_num):
    decoder = VideoDecoder(filename, req_id, fanout_num)
    frames = decoder.decode()
    return [decoder.upload(i, frame) for i, frame in enumerate(frames)]