import base64
from flask import escape
from google.cloud import datastore
from datetime import timedelta
import json
import datetime
import logging
import uuid

def remove(event, context):
  datastore_client = datastore.Client()
  query = datastore_client.query(kind="Merging")
  results = list(query.fetch())

  for res in results:
    print(res.key.id_or_name)
    if ( (res["Date"].replace(tzinfo=None)) <= (datetime.datetime.utcnow() - timedelta(minutes=60*4)) ):
      merge_key = datastore_client.key("Merging", res.key.id_or_name)
      datastore_client.delete(merge_key)

  return "DONE"

