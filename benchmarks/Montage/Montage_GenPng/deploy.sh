#!/bin/bash

set -eu

gcloud functions deploy Montage_GenPng \
    --region northamerica-northeast1 \
    --trigger-topic Montage_GenPng \
    --entry-point handler \
    --timeout 540s \
    --memory 4096MB \
    --runtime python39
