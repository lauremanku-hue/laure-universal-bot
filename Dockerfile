FROM python:3.11

# Installer les dépendances système nécessaires
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
    golang \
    libffi-dev \
    libssl-dev \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Mise à jour de pip et outils de build
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Forcer le téléchargement du binaire neonize pendant la phase de build
# Cela évite l'erreur "UnsupportedPlatform" au démarrage du conteneur
RUN python3 -c "from neonize.download import download; download()" || true

# Copier le reste du code
COPY . .

# Exposer le port (Railway utilise la variable d'environnement PORT)
EXPOSE 3000

# Commande de démarrage avec port dynamique
CMD python3 -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1 --threads 8
