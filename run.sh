docker build -t afadi-question-gen .

# Run with source code mounted for development
docker run -it --rm \
  --name afadi-question-gen  \
  -p 8888:8888 \
  -v $(pwd):/app \
  -v $(pwd)/logs:/app/logs \
  -e MODEL_HOST="http://192.168.71.70:8000" \
  -e MODEL_OPEN_AI_KEY="123" \
  -e DEFAULT_MODEL="sayed0am/Adept-14B-AWQ" \
  afadi-question-gen