# Dockerfile pour le scraper PMMP
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="contact@votredomaine.com"
LABEL description="Scraper pour le Portail Marocain des Marchés Publics"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Dossier de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Installation de Playwright et browsers
RUN playwright install --with-deps chromium

# Copie du code source
COPY . .

# Création des répertoires nécessaires
RUN mkdir -p /app/logs /app/data/archives /app/data/exports

# Permissions
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Port pour l'API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Commande par défaut
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
