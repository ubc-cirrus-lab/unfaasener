#!/bin/bash

set -eu

gcloud functions deploy Montage_Project_Parallel \
    --region northamerica-northeast1 \
    --trigger-topic Montage_Project_Parallel \
    --entry-point handler \
    --timeout 540s \
    --memory 4096MB \
    --runtime python39
