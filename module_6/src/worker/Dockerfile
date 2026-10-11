FROM python:3.11-slim

WORKDIR /app

# Install pinned dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Run as non-root user (USER 1000)
USER 1000

CMD ["python", "consumer.py"]
