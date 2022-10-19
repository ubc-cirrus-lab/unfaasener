#!/bin/bash
set -eu

ACCOUNT_ID=417140135939
REGION=us-east-2

docker build -t $1 .

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
# aws ecr create-repository --repository-name $1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE
docker tag $1:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$1:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$1:latest
