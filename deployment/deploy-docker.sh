#!/bin/bash

echo "Starting build process..."

docker build -t networthlens .
docker compose up -d


echo "Build and deployment completed successfully!"
