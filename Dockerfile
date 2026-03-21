FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    ffmpeg \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Vite build)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy requirements and install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the frontend
RUN npm run build

# Expose the port Railway uses
EXPOSE 3000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "laure_web_launcher:app"]
