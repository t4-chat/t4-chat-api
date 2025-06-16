#!/bin/bash

# Build and start containers in detached mode
docker-compose down -v

docker-compose up --build -d

# Show logs
# docker-compose logs -f 