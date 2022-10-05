#!/bin/bash

set -eu

gcloud functions deploy Montage_GetInput \
    --region northamerica-northeast1 \
    --trigger-http \
    --entry-point handler \
    --runtime python39
