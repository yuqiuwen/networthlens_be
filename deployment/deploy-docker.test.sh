#!/bin/bash


docker build -t networthlens .
docker compose -f docker-compose.dev.yml up -d
