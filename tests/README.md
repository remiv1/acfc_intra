# Tests ACFC - Guide d'Utilisation
=====================================

## Vue d'ensemble

Cette suite de tests couvre toutes les routes et fonctionnalités de l'application ACFC. Les tests sont organisés en plusieurs fichiers spécialisés pour faciliter la maintenance et l'exécution ciblée.

## Structure des Tests

```
tests/
├── test_routes.py          # Tests des routes principales
├── test_security.py        # Tests de sécurité
├── test_blueprints.py      # Tests des modules métiers
├── reports/               # Rapports de tests générés
└── __pycache__/           # Cache Python
```

## Fichiers de Test

### 1. `test_routes.py` - Tests des Routes Principales
- **Routes d'authentification** : login, logout
- **Routes utilisateur** : profil, paramètres, mise à jour
- **Routes administratives** : gestion utilisateurs, health check
- **Routes utilitaires** : changement de mot de passe
- **Gestionnaires d'erreurs** : 4xx, 5xx
- **Tests d'intégration** : workflows complets

### 2. `test_security.py` - Tests de Sécurité
- **Authentification** : protection contre bruteforce, validation
- **Autorisation** : contrôle d'accès, permissions
- **Validation des entrées** : injection SQL, XSS
- **Sessions** : sécurité, fixation de session
- **Mots de passe** : complexité, réutilisation
- **Exposition de données** : fuites d'informations

### 3. `test_blueprints.py` - Tests des Modules Métiers
- **Module Clients** : CRM, gestion des clients
- **Module Catalogue** : produits, catégories
- **Module Commercial** : devis, commandes
- **Module Comptabilité** : facturation, opérations
- **Module Stocks** : inventaire, mouvements
- **Intégration** : workflows inter-modules

## Installation des Dépendances

### Option 1 : Utilisation du script
```bash
python run_tests.py --install-deps
```

### Option 2 : Installation manuelle
```bash
pip install -r requirements-test.txt
```

## Exécution des Tests

### Script d'exécution automatisé
Le script `run_tests.py` offre plusieurs options :

```bash
# Tous les tests
python run_tests.py

# Tests unitaires seulement
python run_tests.py --unit

# Tests d'intégration seulement  
python run_tests.py --integration

# Avec rapport de coverage
python run_tests.py --coverage

# Avec rapport HTML
python run_tests.py --html

# Mode verbeux
python run_tests.py --verbose

# Exécution en parallèle
python run_tests.py --parallel

# Mode rapide (arrêt au premier échec)
python run_tests.py --fast
```

### Exécution directe avec pytest

```bash
# Tous les tests
pytest tests/

# Tests spécifiques
pytest tests/test_routes.py
pytest tests/test_security.py
pytest tests/test_blueprints.py

# Tests avec marqueurs
pytest -m "unit"
pytest -m "integration"
pytest -m "auth"

# Tests avec coverage
pytest --cov=app_acfc --cov-report=html

# Tests en parallèle
pytest -n auto

# Tests verbeux
pytest -v
```

## Organisation par Marqueurs

Les tests utilisent des marqueurs pytest pour faciliter l'exécution ciblée :

- `@pytest.mark.unit` - Tests unitaires
- `@pytest.mark.integration` - Tests d'intégration
- `@pytest.mark.auth` - Tests d'authentification
- `@pytest.mark.user` - Tests utilisateur
- `@pytest.mark.admin` - Tests administrateur
- `@pytest.mark.slow` - Tests lents
- `@pytest.mark.database` - Tests nécessitant une base de données

## Exemples d'Utilisation

### Tests de Développement
```bash
# Tests rapides pendant le développement
python run_tests.py --fast --unit

# Tests d'une route spécifique
pytest tests/test_routes.py::TestAuthenticationRoutes::test_login_post_success -v
```

### Tests de Qualité
```bash
# Suite complète avec coverage
python run_tests.py --coverage --html

# Tests de sécurité uniquement
pytest tests/test_security.py -v
```

### Tests de CI/CD
```bash
# Tests automatisés pour l'intégration continue
pytest tests/ --tb=short --color=yes
```

## Rapports Générés

### Rapport de Coverage
- **Localisation** : `htmlcov/index.html`
- **Contenu** : Pourcentage de code testé, lignes non couvertes
- **Usage** : Identifier les zones nécessitant plus de tests

### Rapport HTML
- **Localisation** : `tests/reports/report.html`
- **Contenu** : Résultats détaillés, temps d'exécution, logs
- **Usage** : Analyse approfondie des résultats de tests

## Configuration

### Variables d'Environnement
Les tests utilisent des variables d'environnement spécifiques :

```bash
TESTING=true
FLASK_ENV=testing
DB_HOST=localhost
DB_USER=test_user
DB_PASSWORD=test_password
DB_NAME=test_acfc
```

### Configuration pytest
Le fichier `pytest.ini` configure :
- Répertoires de tests
- Patterns de fichiers
- Marqueurs personnalisés
- Options par défaut

## Fixtures Disponibles

### Fixtures de Base
- `client` - Client de test Flask
- `mock_user` - Utilisateur de test mocké
- `authenticated_session` - Session utilisateur authentifiée

### Fixtures Spécialisées
- Données de test pour chaque module
- Mocks des services externes
- Configuration de base de données de test

## Bonnes Pratiques

### Écriture de Tests
1. **Isolation** : Chaque test doit être indépendant
2. **Mocking** : Utiliser des mocks pour les dépendances externes
3. **Assertions** : Vérifications claires et spécifiques
4. **Documentation** : Docstrings explicites

### Debugging
```bash
# Tests avec pdb (debugger)
pytest tests/test_routes.py::test_login --pdb

# Tests avec logs
pytest tests/ -s --log-cli-level=DEBUG
```

### Performance
```bash
# Tests avec benchmark
pytest tests/ --benchmark-only

# Profiling des tests lents
pytest tests/ --durations=10
```

## Intégration Continue

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    pip install -r requirements-test.txt
    pytest tests/ --cov=app_acfc --cov-report=xml
```

### Docker
```bash
# Tests dans un container
docker run --rm -v $(pwd):/app -w /app python:3.12 \
  bash -c "pip install -r requirements-test.txt && pytest tests/"
```

## Résolution de Problèmes

### Erreurs Communes

**ImportError des modules**
```bash
# Solution : Vérifier les chemins Python
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app_acfc"
```

**Tests échouent en masse**
```bash
# Solution : Vérifier la configuration de test
pytest tests/ --collect-only
```

**Coverage incomplet**
```bash
# Solution : Ajouter des tests ou exclure des fichiers
pytest --cov=app_acfc --cov-config=.coveragerc
```

## Support et Contribution

### Ajout de Tests
1. Identifier les zones non testées avec coverage
2. Créer des tests dans le fichier approprié
3. Utiliser les fixtures existantes
4. Ajouter des marqueurs appropriés
5. Documenter les nouveaux tests

### Maintenance
- Mettre à jour les mocks lors des changements d'API
- Réviser les tests lors des refactorings
- Maintenir la documentation à jour

---

Pour plus d'informations, consultez la documentation pytest : https://docs.pytest.org/
