FROM python:3.11-slim

WORKDIR /app

# Install pinned dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose web service port
EXPOSE 8080

# Run as non-root user (USER 1000)
USER 1000

CMD ["python", "run.py"]
