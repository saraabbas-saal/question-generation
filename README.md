# Question Generation API

> **Question Generation API** - A FastAPI-based service for generating military assessment questions and answers.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- `.env` file configured (see [Configuration](#configuration))
- Python 3.11+ (for local development)

### Running the API

1. **Clone the repository**
   ```bash
   git clone git@github.com:saal-core/e2-aai-sl-question-generator.git
   
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the API**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

The API will be available at `http://localhost:8888`

## 📋 Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env

# OpenAI-Compatible API Configuration
MODEL_HOST # is the local llm URL
MODEL_API_KEY # is the local llm api key
DEFAULT_MODEL # is the model name

# Optional: Logging Configuration
LOG_LEVEL=INFO
```

### Configuration Notes

- **MODEL_HOST**: Base URL of your LLM service
- **MODEL_API_KEY**: API key for authentication
- **DEFAULT_MODEL**: Model name to use for question generation
- **MODEL_HOST**: OpenAI-compatible endpoint URL
- **MODEL_API_KEY**: API key for OpenAI-compatible service
- **DEFAULT_MODEL**: Model name for OpenAI-compatible service

## 🔧 API Endpoints

### Generate Questions

**POST** `/generate-questions`

Generate assessment questions based on teaching points.

#### Request Body
```json
{
  "teaching_point_en": "Explain the AFADI LTEM Environment framework",
  "teaching_point_ar": "شرح إطار عمل بيئة AFADI LTEM",
  "context": "Focus on tactical applications",
  "question_type": "MULTICHOICE",
  "language": "en",
  "bloom_level": "UNDERSTAND",
  "number_of_distractors": 3,
  "number_of_correct_answers": 1
}
```

#### Supported Parameters

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `question_type` | string | `MULTICHOICE`, `MULTI_SELECT`, `TRUE_FALSE`, `TRUE_FALSE_JUSTIFICATION` | Type of question to generate |
| `language` | string | `en`, `ar` | Language for questions |
| `bloom_level` | string | `REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE` | Bloom's taxonomy level |
| `number_of_distractors` | integer | 2-6 | Number of incorrect options |
| `number_of_correct_answers` | integer | 1-4 | Number of correct answers (for `MULTI_SELECT`) |

#### Response Example
```json
{
  "questions": [
    {
      "question_number": 1,
      "question": "What is the primary purpose of the AFADI LTEM framework?",
      "options": [
        {"key": "A", "value": "Training management"},
        {"key": "B", "value": "Equipment maintenance"},
        {"key": "C", "value": "Personnel evaluation"},
        {"key": "D", "value": "Strategic planning"}
      ],
      "answer": ["A"],
      "model_answer": null
    }
  ],
  "teaching_point": "Explain the AFADI LTEM Environment framework",
  "question_type": "MULTICHOICE",
  "language": "en",
  "bloom_level": "UNDERSTAND"
}
```

### Health Check

**GET** `/health`

Check the API service status.

#### Response
```json
{
  "status": "healthy",
  "service": "AFADI Question Generation API",
  "version": "2.0.0",
  "baml_enabled": true
}
```

### Legacy Text Generation

**POST** `/generate`

Generate text based on custom prompts (legacy endpoint).

#### Request Body
```json
{
  "prompt": "Generate a question about military leadership"
}
```

## 🐳 Docker Configuration

### Build and Run

The `run.sh` script handles the complete Docker workflow:

```bash
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
  --env-file .env \
  afadi-question-gen
```

### Docker Features

- **Development Mode**: Source code is mounted for live reloading
- **Logging**: Logs are persisted in `./logs` directory
- **Environment**: Configuration loaded from `.env` file
- **Port Mapping**: API accessible on port 8888
- **Auto-cleanup**: Container is removed when stopped (`--rm`)

### Manual Docker Commands

```bash
# Build image
docker build -t afadi-question-gen .

# Run container
docker run -it --rm \
  --name afadi-question-gen \
  -p 8888:8888 \
  --env-file .env \
  afadi-question-gen

# View logs
docker logs afadi-question-gen

# Stop container
docker stop afadi-question-gen
```

## 🔍 Testing

### Health Check
```bash
curl http://localhost:8888/health
```

### Generate Questions
```bash
curl -X POST http://localhost:8888/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "teaching_point_en": "Military leadership principles",
    "question_type": "MULTICHOICE",
    "language": "en",
    "bloom_level": "UNDERSTAND",
    "number_of_distractors": 3
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8888/generate-questions",
    json={
        "teaching_point_en": "Air defense tactics",
        "question_type": "TRUE_FALSE",
        "language": "en",
        "bloom_level": "APPLY"
    }
)

print(response.json())
```
