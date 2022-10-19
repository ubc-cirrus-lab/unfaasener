#!/bin/bash

set -eu

gcloud functions deploy DNAVisualization \
    --region northamerica-northeast1 \
    --trigger-http \
    --timeout 20s \
    --entry-point handler \
    --memory 512MB \
    --runtime python39
