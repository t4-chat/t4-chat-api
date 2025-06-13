#!/bin/bash

# Build and start containers in detached mode
docker-compose up --build

# Show logs
docker-compose logs -f 