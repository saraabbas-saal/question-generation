
docker build -t afadi-question-gen .

# 2. Run the container
docker run -it --rm \
  --name afadi-question-gen  \
  -p 8888:8888 \
  -v $(pwd)/logs:/app/logs \
  -e MODEL_HOST="http://192.168.71.70:8000" \
  -e MODEL_OPEN_AI_KEY="123" \
  -e DEFAULT_MODEL="sayed0am/Adept-14B-AWQ" \
  afadi-question-gen

