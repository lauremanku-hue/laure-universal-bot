FROM python:3.11-bookworm

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    ca-certificates \
    curl \
    wget \
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

# FORCER LE TÉLÉCHARGEMENT DU BINAIRE NEONIZE MANUELLEMENT
# Cela résout définitivement l'erreur "UnsupportedPlatform"
RUN NEONIZE_PATH=$(python3 -c "import neonize; import os; print(os.path.dirname(neonize.__file__))") && \
    cd $NEONIZE_PATH && \
    wget https://github.com/krypton-byte/neonize/releases/download/0.3.15.post0/neonize-linux-amd64.so -O neonize-linux-amd64.so && \
    chmod +x neonize-linux-amd64.so

# Copier le reste du code
COPY . .

# Exposer le port (Railway utilise la variable d'environnement PORT)
EXPOSE 3000

# Commande de démarrage avec port dynamique
CMD python3 -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1 --threads 8
