#!/bin/bash

set -e

echo "🚀 AFADI Question Generation System Deployment"
echo "============================================="

# Build Docker image
echo "📦 Building Docker image..."
docker build -t question-generator:v2 .

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker stop question-generator 2>/dev/null || true
docker rm question-generator 2>/dev/null || true

# Create logs directory
mkdir -p logs

# Run with enhanced configuration
echo "🏃 Starting enhanced AFADI Question Generation service..."
docker run -it --rm \
  --name question-generator \
  -p 8088:8088 \
  -v $(pwd):/app \
  -v $(pwd)/.env:/app/.env \
  -e MODEL_HOST="${MODEL_HOST:-http://192.168.71.70:8000}" \
  -e MODEL_OPEN_AI_KEY="${MODEL_OPEN_AI_KEY:-123}" \
  -e DEFAULT_MODEL="${DEFAULT_MODEL:-sayed0am/Adept-14B-AWQ}" \
  question-generator:v2

echo "⏳ Waiting for service to start..."
sleep 10

# Health check
echo "🏥 Running health check..."
if curl -f http://localhost:8088/health; then
    echo "✅ Service is healthy and ready!"
    echo "📊 API Documentation: http://localhost:8088/docs"
    echo "🔍 Health Check: http://localhost:8088/health"
    echo "📝 Question Types: http://localhost:8088/question-types"
else
    echo "❌ Service health check failed"
    echo "📋 Checking logs..."
    docker logs question-generator
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "Service is running at: http://localhost:8088"