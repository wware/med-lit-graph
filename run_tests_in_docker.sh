#!/bin/bash -xe
# Run tests in Docker container to avoid port conflicts
# Services communicate via internal Docker network

echo "=========================================="
echo "Running tests in Docker container"
echo "=========================================="

# Stop any existing test containers
docker compose -f docker-compose.test.yml down 2>/dev/null || true

# Build and run tests
docker compose -f docker-compose.test.yml up --build test-runner

# Capture exit code
EXIT_CODE=$?

# Cleanup
docker compose -f docker-compose.test.yml down

exit $EXIT_CODE
