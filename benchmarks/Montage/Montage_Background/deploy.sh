#!/bin/bash

set -eu

gcloud functions deploy Montage_Background \
    --region northamerica-northeast1 \
    --trigger-topic Montage_Background \
    --entry-point handler \
    --timeout 540s \
    --memory 8192MB \
    --runtime python39
