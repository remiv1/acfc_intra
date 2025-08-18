# Utiliser une image Python officielle comme base
FROM python:3.12-bookworm

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers requirements.txt dans le conteneur
COPY requirements-app.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers de l'application dans le conteneur
COPY app_acfc/ /app

# Exposer le port 5000
EXPOSE 5000

# Définir la commande pour démarrer l'application avec wisig
CMD ["python", "application.py"]