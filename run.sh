#!/bin/bash

echo "🚀 Building AFADI Question Generation API..."

# Build the Docker image
docker build -t afadi-question-gen .

echo "🔧 Starting API server..."

# Run with source code mounted for development
docker run  --rm \
  --name afadi-question-gen  \
  -p 8888:8888 \
  --env-file .env \
  afadi-question-gen

echo "📝 Notes:"
echo "  - API will be available at http://localhost:8888"
echo "  - Health check: http://localhost:8888/health"
echo "  - BAML status: http://localhost:8888/baml-status"
echo "  - BAML is not available in this setup - using legacy parsing"
echo "  - To enable BAML: install baml-py and run 'baml-cli generate'"