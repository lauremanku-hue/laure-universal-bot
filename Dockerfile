FROM python:3.11-slim

# Installer les dépendances système nécessaires pour neonize, sqlite et libmagic
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    ca-certificates \
    curl \
    gcc \
    python3-dev \
    g++ \
    make \
    libmagic1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Copier le reste du code
COPY . .

# Exposer le port par défaut (Railway gère le mapping)
EXPOSE 3000

# Commande de démarrage avec port dynamique (via shell pour expansion de $PORT)
CMD python3 -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1 --threads 8
