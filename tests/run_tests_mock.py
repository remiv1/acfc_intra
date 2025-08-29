#!/usr/bin/env python3
"""
Script de test complet pour l'application ACFC
==============================================

Ce script exécute tous les tests de l'application en s'assurant que
l'environnement est correctement configuré et que tous les mocks sont en place.

Fonctionnalités :
- Configuration automatique de l'environnement de test
- Exécution des tests avec isolation complète de la base de données
- Rapport de couverture détaillé
- Tests par catégorie (unitaires, intégration, e2e)

Utilisation :
    python run_tests_mock.py [--unit] [--integration] [--e2e] [--coverage]

Auteur : ACFC Development Team
Version : 1.0
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Any

# Configuration des variables d'environnement pour les tests
def setup_test_environment():
    """Configure l'environnement de test avec des valeurs mockées."""
    test_env = {
        'TESTING': 'true',
        'DB_HOST': 'mock_host',
        'DB_PORT': '3306',
        'DB_NAME': 'mock_db',
        'DB_USER': 'mock_user',
        'DB_PASSWORD': 'mock_password',
        'MYSQL_ROOT_PASSWORD': 'mock_root_password',
        'MYSQL_DATABASE': 'mock_db',
        'MYSQL_USER': 'mock_user',
        'MYSQL_PASSWORD': 'mock_password',
        'MONGO_INITDB_DATABASE': 'mock_logs',
        'MONGO_INITDB_ROOT_USERNAME': 'mock_admin',
        'MONGO_INITDB_ROOT_PASSWORD': 'mock_password',
        'MONGO_HOST': 'mock_mongo',
        'MONGO_PORT': '27017',
        'SESSION_PASSKEY': 'mock_session_key',
        'API_SECRET': 'mock_api_secret',
        'FLASK_HOST': '127.0.0.1',
        'FLASK_PORT': '5000',
        'FLASK_ENV': 'testing'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    print("✅ Environnement de test configuré avec des valeurs mockées")


def run_tests(test_type: Any=None, coverage: bool=False):
    """Exécute les tests avec la configuration appropriée."""
    
    # Dossier de base du projet (parent du dossier tests)
    project_root = Path(__file__).parent.parent
    
    # Commande pytest de base
    cmd = [sys.executable, '-m', 'pytest', '-v']
    
    # Ajout de la couverture si demandée
    if coverage:
        cmd.extend([
            '--cov=app_acfc',
            '--cov-report=html:htmlcov_tests',
            '--cov-report=term-missing',
            '--cov-fail-under=70'
        ])
    
    # Sélection des tests selon le type
    if test_type == 'unit':
        cmd.append(str(project_root / 'tests' / 'unit'))
        print("🧪 Exécution des tests unitaires...")
    elif test_type == 'integration':
        cmd.append(str(project_root / 'tests' / 'integration'))
        print("🔗 Exécution des tests d'intégration...")
    elif test_type == 'e2e':
        cmd.append(str(project_root / 'tests' / 'e2e'))
        print("🌐 Exécution des tests end-to-end...")
    else:
        cmd.extend([str(project_root / 'tests' / 'unit'), str(project_root / 'tests' / 'integration')])
        print("🚀 Exécution de tous les tests...")
    
    # Ajout d'options pytest pour améliorer la sortie
    cmd.extend([
        '--tb=short',  # Traceback court
        '--strict-markers',  # Marqueurs stricts
        '--disable-warnings',  # Désactiver les warnings pour une sortie plus claire
    ])
    
    # Exécution des tests
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        
        if result.returncode == 0:
            print("✅ Tous les tests sont passés avec succès !")
            if coverage:
                print("📊 Rapport de couverture généré dans htmlcov_tests/")
        else:
            print("❌ Certains tests ont échoué")
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        print("❌ pytest n'est pas installé. Installez-le avec: pip install pytest pytest-cov")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        sys.exit(1)


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description='Exécute les tests ACFC avec mocks complets')
    parser.add_argument('--unit', action='store_true', help='Exécuter uniquement les tests unitaires')
    parser.add_argument('--integration', action='store_true', help='Exécuter uniquement les tests d\'intégration')
    parser.add_argument('--e2e', action='store_true', help='Exécuter uniquement les tests end-to-end')
    parser.add_argument('--coverage', action='store_true', help='Générer un rapport de couverture')
    
    args = parser.parse_args()
    
    # Configuration de l'environnement
    setup_test_environment()
    
    # Détermination du type de test
    test_type = None
    if args.unit:
        test_type = 'unit'
    elif args.integration:
        test_type = 'integration'
    elif args.e2e:
        test_type = 'e2e'
    
    # Exécution des tests
    run_tests(test_type, args.coverage)


if __name__ == '__main__':
    main()
