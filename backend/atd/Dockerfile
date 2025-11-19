# Use official Python base image
FROM python:3.12-slim

# Prevent Python from writing pyc files / buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory inside container
WORKDIR /app

# Install system dependencies for mysqlclient & cryptography
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file into container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose Django port
EXPOSE 8000

# Run Django dev server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "atd.wsgi:application", "--bind", "0.0.0.0:8000"]