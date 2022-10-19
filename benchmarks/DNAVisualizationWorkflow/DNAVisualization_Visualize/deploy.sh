#!/bin/bash

set -eu

gcloud functions deploy DNAVisualization_Visualize \
    --region northamerica-northeast1 \
    --trigger-topic DNAVisualization_Visualize \
    --entry-point handler \
    --timeout 20s \
    --memory 512MB \
    --runtime python310
