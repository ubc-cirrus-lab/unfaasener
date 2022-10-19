import uuid
import os

from google.cloud import storage
from dna_features_viewer import BiopythonTranslator


"""
Sample input json
{
    "gen_file_name": "sequence_2.gb"
}
"""
def handler(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    gen_file_name = request_json['gen_file_name']
    req_id = uuid.uuid4().hex

    local_gen_filename = f'/tmp/genbank-{req_id}.gb'
    local_result_filename = f'/tmp/result-{req_id}.png'

    cli = storage.Client()
    bucket = cli.bucket('dna_visualization')
    blob = bucket.blob(f'gen_bank/{gen_file_name}')
    blob.download_to_filename(local_gen_filename)

    graphic_record = BiopythonTranslator().translate_record(local_gen_filename)
    ax, _ = graphic_record.plot(figure_width=10, strand_in_label_threshold=7)
    ax.figure.tight_layout()
    ax.figure.savefig(local_result_filename)

    blob = bucket.blob(f'result/{req_id}.png')
    blob.upload_from_filename(local_result_filename)

    os.remove(local_gen_filename)
    os.remove(local_result_filename)

    return {
        'message': f'uploaded to {req_id}'
    }
