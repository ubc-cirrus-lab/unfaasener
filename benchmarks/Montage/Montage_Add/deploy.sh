#!/bin/bash

set -eu

gcloud functions deploy Montage_Add \
    --region northamerica-northeast1 \
    --trigger-topic Montage_Add \
    --entry-point handler \
    --timeout 540s \
    --memory 8192MB \
    --runtime python39
