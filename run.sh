#!/bin/bash

echo "🚀 Building AFADI Question Generation API..."

# Build the Docker image
docker build -t afadi-question-gen .

echo "🔧 Starting API server..."

# Run with source code mounted for development
docker run -it --rm \
  --name afadi-question-gen  \
  -p 8888:8888 \
  -v $(pwd):/app \
  -v $(pwd)/logs:/app/logs \
  -e MODEL_HOST="http://192.168.71.70:8080" \
  -e MODEL_OPEN_AI_KEY="123" \
  -e DEFAULT_MODEL="adept3" \
  -e OPENAI_API_URL="http://192.168.71.70:8080/v1" \
  -e OPENAI_API_KEY="123" \
  -e OPENAI_MODEL="adept3" \
  afadi-question-gen

echo "📝 Notes:"
echo "  - API will be available at http://localhost:8888"
echo "  - Health check: http://localhost:8888/health"
echo "  - BAML status: http://localhost:8888/baml-status"
echo "  - BAML is not available in this setup - using legacy parsing"
echo "  - To enable BAML: install baml-py and run 'baml-cli generate'"