#!/usr/bin/env python3
"""
Script d'exécution des tests ACFC
=================================

Script utilitaire pour exécuter les tests de l'application ACFC
avec différentes options et configurations.

Usage:
    python run_tests.py                    # Tous les tests
    python run_tests.py --unit             # Tests unitaires seulement
    python run_tests.py --integration      # Tests d'intégration seulement
    python run_tests.py --coverage         # Avec rapport de coverage
    python run_tests.py --html             # Rapport HTML
    python run_tests.py --verbose          # Mode verbeux
    python run_tests.py --parallel         # Exécution parallèle

Exemples:
    python run_tests.py --unit --coverage
    python run_tests.py --integration --html
    python run_tests.py --verbose --parallel
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def get_project_root():
    """Retourne le répertoire racine du projet."""
    return Path(__file__).parent.absolute()

def install_test_dependencies():
    """Installe les dépendances de test si nécessaire."""
    print("🔧 Vérification des dépendances de test...")
    
    try:
        import pytest   # type: ignore
        print("✅ pytest déjà installé")
    except ImportError:
        print("📦 Installation des dépendances de test...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements-test.txt"
        ], check=True)
        print("✅ Dépendances installées")

def run_tests(args: argparse.Namespace) -> int:
    """Exécute les tests avec les options spécifiées."""
    project_root = get_project_root()
    os.chdir(project_root)
    
    # Construction de la commande pytest
    cmd = [sys.executable, "-m", "pytest"]
    
    # Options selon les arguments
    if args.unit:
        cmd.extend(["-m", "unit"])
        print("🧪 Exécution des tests unitaires...")
    elif args.integration:
        cmd.extend(["-m", "integration"])
        print("🔗 Exécution des tests d'intégration...")
    else:
        print("🚀 Exécution de tous les tests...")
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=app_acfc", "--cov-report=term", "--cov-report=html"])
        print("📊 Génération du rapport de coverage...")
    
    if args.html:
        cmd.extend(["--html=tests/reports/report.html", "--self-contained-html"])
        print("📄 Génération du rapport HTML...")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
        print("⚡ Exécution en parallèle...")
    
    if args.fast:
        cmd.extend(["-x", "--tb=short"])
        print("🏃 Mode rapide (arrêt au premier échec)...")
    
    # Options par défaut
    cmd.extend([
        "--color=yes",
        "--tb=short" if not args.verbose else "--tb=long"
    ])
    
    # Ajout du répertoire de tests
    cmd.append("tests/")
    
    # Exécution
    print(f"🎯 Commande: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ Erreur: pytest n'est pas installé")
        print("💡 Exécutez: pip install -r requirements-test.txt")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        return 130

def create_reports_directory():
    """Crée le répertoire pour les rapports s'il n'existe pas."""
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Script d'exécution des tests ACFC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python run_tests.py                     # Tous les tests
  python run_tests.py --unit --coverage   # Tests unitaires avec coverage
  python run_tests.py --integration --html # Tests d'intégration avec rapport HTML
  python run_tests.py --fast --parallel   # Mode rapide en parallèle
        """
    )
    
    # Types de tests
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit", action="store_true",
        help="Exécuter seulement les tests unitaires"
    )
    test_group.add_argument(
        "--integration", action="store_true",
        help="Exécuter seulement les tests d'intégration"
    )
    
    # Options de rapport
    parser.add_argument(
        "--coverage", action="store_true",
        help="Générer un rapport de coverage"
    )
    parser.add_argument(
        "--html", action="store_true",
        help="Générer un rapport HTML"
    )
    
    # Options d'exécution
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Mode verbeux"
    )
    parser.add_argument(
        "--parallel", "-p", action="store_true",
        help="Exécution en parallèle"
    )
    parser.add_argument(
        "--fast", "-f", action="store_true",
        help="Mode rapide (arrêt au premier échec)"
    )
    
    # Options de maintenance
    parser.add_argument(
        "--install-deps", action="store_true",
        help="Installer les dépendances de test"
    )
    
    args = parser.parse_args()
    
    print("🧪 ACFC - Exécution des Tests")
    print("=" * 30)
    
    # Installation des dépendances si demandée
    if args.install_deps:
        install_test_dependencies()
        return 0
    
    # Création du répertoire de rapports
    if args.html:
        create_reports_directory()
    
    # Vérification de pytest
    try:
        import pytest   # type: ignore
    except ImportError:
        print("❌ pytest n'est pas installé")
        print("💡 Utilisez --install-deps pour installer les dépendances")
        return 1
    
    # Exécution des tests
    return_code = run_tests(args)
    
    # Messages de fin
    if return_code == 0:
        print("\n✅ Tous les tests sont passés avec succès!")
        if args.coverage:
            print("📊 Rapport de coverage: htmlcov/index.html")
        if args.html:
            print("📄 Rapport HTML: tests/reports/report.html")
    else:
        print(f"\n❌ Les tests ont échoué (code: {return_code})")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
