import base64
import datetime
import json
import logging
import os
from sys import getsizeof
import uuid
import cv2

from google.cloud import storage, pubsub_v1

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = '***'

def streaming(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    routing_data = event['attributes']['routing']
    routing = routing_data[2]
    req_id = event['attributes']['reqID']
    filename = json.loads(base64.b64decode(event['data']).decode('utf-8'))['data']['videoName']
    fanout_num = json.loads(base64.b64decode(event['data']).decode('utf-8'))['data']['fanoutNum']
    video_name = VideoAnalytics_Streaming(filename, req_id)
    message = json.dumps({
        'data': {'videoName': video_name, 'fanoutNum': fanout_num}
    }).encode('utf-8')
    msg_id = uuid.uuid4().hex

    next_fn = 'VideoAnalytics_Decoder'
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
    logging.warning(req_id)

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
