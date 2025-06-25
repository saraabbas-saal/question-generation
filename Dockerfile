FROM python:3.10-slim

WORKDIR /app

EXPOSE 5056

# Install system dependencies needed for building Python packages
RUN apt-get update && \
    apt-get install -y gcc g++ make curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the download script
COPY download_model.py download_model.py

# Make the script executable
RUN chmod +x download_model.py

# Download the model during build time
RUN python download_model.py
# Copy the rest of the application
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

