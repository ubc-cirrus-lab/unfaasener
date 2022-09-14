import json
from datetime import datetime
import boto3
from sklearn import datasets
import os

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    # Get input
    print("Create Dataset Function")
    print(event)
    n_samples = json.loads(event['body'])['data']['n_samples']
    reqID = json.loads(event['body'])['data']['reqID']
    
    bucket = s3.Bucket("regression-tuning-storage")
    x, y = datasets.make_regression(n_samples=n_samples,
                                    n_features=1,
                                    n_informative=1,
                                    n_targets=1,
                                    bias=3.0,
                                    noise=1.0)
    # just make sure data is in the right format, i.e. one feature
    assert x.shape[1] == 1
    # write to file, tab separated
    path = "/tmp/" + "dataset.txt"
    with open(path, "w") as _file:
        for _ in range(len(x)):
            _file.write("{}\t{}\n".format(x[_][0], y[_]))
    upPath = str(reqID)+"-dataset.txt"
    bucket.upload_file("/tmp/dataset.txt", upPath)
    os.remove(path)

   # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'upPath': upPath, 'reqID': reqID},
        })
    }