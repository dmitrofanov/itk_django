FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy database wait script
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Copy project
COPY . .

# Create static files directory
RUN mkdir -p /app/staticfiles

# Default command (will be overridden in docker-compose.yml)
# Use runserver for development, gunicorn for production
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


