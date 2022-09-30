import base64
import datetime
import json
import logging
import os
from sys import getsizeof
import tempfile
import uuid

import cv2
from google.cloud import storage, pubsub_v1

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
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


def decode(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    routing_data = event['attributes']['routing']
    routing = routing_data[3]
    req_id = event['attributes']['reqID']
    video_name = json.loads(base64.b64decode(event['data']).decode('utf-8'))['data']['videoName']
    fanout_num = json.loads(base64.b64decode(event['data']).decode('utf-8'))['data']['fanoutNum']
    filenames = VideoAnalytics_Decoder(video_name, req_id, fanout_num)
    for i, filename in enumerate(filenames):
        message = json.dumps({
            'data': {'imageName': filename}
        }).encode('utf-8')
        msg_id = uuid.uuid4().hex

        next_fn = 'VideoAnalytics_Recognition'
        if routing == '0':
            topic_path = publisher.topic_path(PROJECT_ID, next_fn)
            publish_future = publisher.publish(
                topic_path,
                data=message,
                reqID=req_id,
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msg_id,
                msgSize=str(getsizeof(video_name)),
                routing=routing_data.encode('utf-8'),
            )
        else:
            vm_topic = f'vmTopic{ord(routing) - 64}'
            topic_path = publisher.topic_path(PROJECT_ID, vm_topic)
            publish_future = publisher.publish(
                topic_path,
                data=message,
                reqID=req_id,
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msg_id,
                msgSize=str(getsizeof(video_name)),
                invokedFunction=next_fn,
                routing=routing_data.encode('utf-8'),
            )
        publish_future.result()
        logging.warning(f'{req_id} {i}th frame done')


def VideoAnalytics_Decoder(filename, req_id, fanout_num):
    decoder = VideoDecoder(filename, req_id, fanout_num)
    frames = decoder.decode()
    return [decoder.upload(i, frame) for i, frame in enumerate(frames)]
