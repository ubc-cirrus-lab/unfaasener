#!/bin/bash

set -eu

gcloud functions deploy Montage_Overlaps \
    --region northamerica-northeast1 \
    --trigger-topic Montage_Overlaps \
    --entry-point handler \
    --timeout 540s \
    --memory 2048MB \
    --runtime python39
