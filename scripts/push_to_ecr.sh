#!/bin/bash
# Build, tag, and push Docker image to AWS ECR
# Usage: ./scripts/push_to_ecr.sh <aws_account_id> <region> <repo_name>

set -e
AWS_ACCOUNT_ID=$1
REGION=$2
REPO_NAME=$3

if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$REGION" ] || [ -z "$REPO_NAME" ]; then
  echo "Usage: $0 <aws_account_id> <region> <repo_name>"
  exit 1
fi

ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

echo "Building Docker image..."
docker build -t $REPO_NAME:latest .

echo "Tagging image..."
docker tag $REPO_NAME:latest $ECR_URL:latest

echo "Pushing image to ECR..."
docker push $ECR_URL:latest

echo "Image pushed: $ECR_URL:latest"
