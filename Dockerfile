FROM python:3.10-slim

# Installer les dépendances système nécessaires pour neonize et sqlite
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Exposer le port par défaut (Railway gère le mapping)
EXPOSE 3000

# Commande de démarrage avec port dynamique (via shell pour expansion de $PORT)
CMD python3 -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1 --threads 8
