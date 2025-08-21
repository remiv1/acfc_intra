# Docker Compose CI/CD Workflow

Ce dossier contient un workflow GitHub Actions pour valider le bon fonctionnement de l'infrastructure Docker Compose de l'application ACFC.

## 📋 Contenu

- `.github/workflows/docker-ci.yml` - Workflow GitHub Actions principal
- `test-docker-ci.sh` - Script de test local (Linux/macOS)
- `test-docker-ci.ps1` - Script de test local (Windows PowerShell)
- `.env.ci` - Variables d'environnement pour CI

## 🚀 Fonctionnalités du Workflow

### Déclencheurs
- **Push** sur les branches `main`, `develop`, `sprint_interface`
- **Pull Request** vers `main`, `develop` 
- **Manuel** via l'interface GitHub Actions

### Étapes de Validation

1. **Validation syntaxe** - Vérification de `docker-compose.yml`
2. **Build parallèle** - Construction de toutes les images Docker
3. **Démarrage ordonné** - Lancement des services avec vérification de santé
4. **Tests d'intégration** - Vérification des endpoints et connectivité DB
5. **Collecte des logs** - Sauvegarde des logs pour diagnostic
6. **Nettoyage** - Suppression des conteneurs et volumes

### Services Testés

- **acfc-app** (Flask) - Application web principale
- **acfc-db** (MariaDB) - Base de données relationnelle  
- **acfc-logs** (MongoDB) - Base de données de logs
- **acfc-nginx** - Reverse proxy et serveur statique

## 🧪 Tests Locaux

### Windows (PowerShell)
```powershell
.\test-docker-ci.ps1
```

### Linux/macOS (Bash)
```bash
chmod +x test-docker-ci.sh
./test-docker-ci.sh
```

## 📊 Endpoints de Santé

Le workflow utilise plusieurs endpoints pour vérifier l'état des services :

### `/health` - Santé de l'application
```json
{
  "status": "healthy",
  "timestamp": "2025-08-21T22:30:00",
  "services": {
    "database": "ok",
    "application": "ok"
  },
  "version": "1.0"
}
```

**Codes de retour :**
- `200` - Tous les services sont OK
- `503` - Service dégradé (DB inaccessible)
- `500` - Erreur interne

### `/` - Endpoint principal
Vérifie que l'application Flask répond et que l'authentification fonctionne.

## 🔧 Configuration

### Variables d'Environnement CI

Le workflow crée automatiquement un fichier `.env` avec les variables suivantes :

```bash
# Base de données
DB_HOST=acfc-db
DB_PORT=3306
DB_NAME=acfc
DB_USER=acfc_user
DB_PASSWORD=acfc_password_ci
DB_ROOT_PASSWORD=root_password_ci

# MongoDB
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=mongo_password_ci
MONGO_INITDB_DATABASE=logs
MONGO_HOST=acfc-logs
MONGO_PORT=27017

# Flask
FLASK_ENV=testing
```

### Secrets GitHub (Optionnel)

Pour publier les images sur Docker Hub :
- `DOCKERHUB_USERNAME` - Nom d'utilisateur Docker Hub
- `DOCKERHUB_TOKEN` - Token d'accès Docker Hub

## 📋 Logs et Artifacts

En cas d'échec, le workflow sauvegarde automatiquement :
- `logs/app.log` - Logs de l'application Flask
- `logs/database.log` - Logs MariaDB
- `logs/mongodb.log` - Logs MongoDB  
- `logs/nginx.log` - Logs Nginx
- `logs/containers-status.txt` - État des conteneurs

Les artifacts sont conservés 7 jours et téléchargeables depuis l'interface GitHub Actions.

## 🛠️ Dépannage

### Erreurs Courantes

1. **Timeout de démarrage**
   - Vérifier les ressources disponibles (RAM, CPU)
   - Augmenter `COMPOSE_HTTP_TIMEOUT` dans le workflow

2. **Échec de connexion DB**
   - Vérifier le script d'initialisation `mariadb/init_db.sql`
   - Contrôler les variables d'environnement

3. **Endpoint /health inaccessible**
   - Vérifier que Flask démarre correctement
   - Consulter les logs de l'application

### Commandes de Debug Local

```bash
# Status des conteneurs
docker compose ps

# Logs en temps réel
docker compose logs -f

# Tester la connectivité
curl -v http://localhost:5000/health
curl -v http://localhost:5000/

# Inspecter un conteneur
docker compose exec acfc-app bash
```

## 📈 Métriques

Le workflow mesure :
- **Temps de build** des images
- **Temps de démarrage** des services  
- **Temps de réponse** des endpoints
- **Utilisation des ressources**

## 🔄 Intégration Continue

Le workflow est conçu pour :
- ✅ Bloquer les merges en cas d'échec
- ✅ Fournir un feedback rapide (< 5 minutes)
- ✅ Être reproductible localement
- ✅ Collecter des métriques de performance
- ✅ Nettoyer automatiquement les ressources

---

**Note :** Ce workflow remplace les tests manuels de validation Docker et garantit la reproductibilité des déploiements.
