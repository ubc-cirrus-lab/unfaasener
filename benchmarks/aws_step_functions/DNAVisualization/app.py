import uuid
import os

import boto3
from dna_features_viewer import BiopythonTranslator


"""
Sample input json
{
    "gen_file_name": "sequence_2.gb"
}
"""
def handler(event, context):
    gen_file_name = event['gen_file_name']
    req_id = uuid.uuid4().hex

    local_gen_filename = f'/tmp/genbank-{req_id}.gb'
    local_result_filename = f'/tmp/result-{req_id}.png'

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('dnavisualization')
    bucket.download_file(f'gen_bank/{gen_file_name}', local_gen_filename)

    graphic_record = BiopythonTranslator().translate_record(local_gen_filename)
    ax, _ = graphic_record.plot(figure_width=10, strand_in_label_threshold=7)
    ax.figure.tight_layout()
    ax.figure.savefig(local_result_filename)

    bucket.upload_file(local_result_filename, f'result/{req_id}.png')

    os.remove(local_gen_filename)
    os.remove(local_result_filename)

    return {
        'message': f'uploaded to {req_id}'
    }
