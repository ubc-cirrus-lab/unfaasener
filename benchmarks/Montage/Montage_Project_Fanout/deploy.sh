#!/bin/bash

set -eu

gcloud functions deploy Montage_Project_Fanout \
    --region northamerica-northeast1 \
    --trigger-topic Montage_Project_Fanout \
    --entry-point handler \
    --runtime python39
