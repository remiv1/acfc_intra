#!/bin/bash

# Script de lancement des tests ACFC
# ===================================

set -e

echo "🚀 Lancement des Tests ACFC"
echo "============================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage coloré
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification de l'environnement
print_status "Vérification de l'environnement..."

if ! command -v python &> /dev/null; then
    print_error "Python n'est pas installé ou non trouvé dans PATH"
    exit 1
fi

if ! python -c "import pytest" &> /dev/null; then
    print_error "pytest n'est pas installé. Installation..."
    pip install pytest pytest-cov pytest-html
fi

# Installation des dépendances si nécessaire
if [ -f "requirements-test.txt" ]; then
    print_status "Installation des dépendances de test..."
    pip install -r requirements-test.txt
fi

if [ -f "requirements-app.txt" ]; then
    print_status "Installation des dépendances application..."
    pip install -r requirements-app.txt
fi

# Fonctions de test
run_unit_tests() {
    print_status "Exécution des tests unitaires..."
    if pytest tests/unit/ -v --tb=short -m unit; then
        print_success "Tests unitaires réussis"
        return 0
    else
        print_error "Échec des tests unitaires"
        return 1
    fi
}

run_integration_tests() {
    print_status "Exécution des tests d'intégration..."
    if pytest tests/integration/ -v --tb=short -m integration; then
        print_success "Tests d'intégration réussis"
        return 0
    else
        print_error "Échec des tests d'intégration"
        return 1
    fi
}

run_e2e_tests() {
    print_status "Exécution des tests end-to-end..."
    if pytest tests/e2e/ -v --tb=short -m e2e; then
        print_success "Tests end-to-end réussis"
        return 0
    else
        print_error "Échec des tests end-to-end"
        return 1
    fi
}

run_demo_tests() {
    print_status "Exécution des tests de démonstration..."
    if pytest tests/demo/ -v -s --tb=short -m demo; then
        print_success "Tests de démonstration réussis"
        return 0
    else
        print_error "Échec des tests de démonstration"
        return 1
    fi
}

run_coverage_tests() {
    print_status "Exécution des tests avec couverture..."
    if pytest --cov=app_acfc --cov=api_acfc --cov-report=html --cov-report=xml --cov-report=term; then
        print_success "Tests de couverture réussis"
        print_status "Rapport HTML généré dans htmlcov/"
        return 0
    else
        print_error "Échec des tests de couverture"
        return 1
    fi
}

run_qrcode_tests() {
    print_status "Exécution des tests QR Code..."
    if pytest -m qrcode -v --tb=short; then
        print_success "Tests QR Code réussis"
        return 0
    else
        print_error "Échec des tests QR Code"
        return 1
    fi
}

run_printing_tests() {
    print_status "Exécution des tests d'impression..."
    if pytest -m printing -v --tb=short; then
        print_success "Tests d'impression réussis"
        return 0
    else
        print_error "Échec des tests d'impression"
        return 1
    fi
}

run_all_tests() {
    print_status "Exécution de tous les tests..."
    local failed=0
    
    run_unit_tests || failed=$((failed + 1))
    run_integration_tests || failed=$((failed + 1))
    run_e2e_tests || failed=$((failed + 1))
    
    if [ $failed -eq 0 ]; then
        print_success "Tous les tests ont réussi!"
        return 0
    else
        print_error "$failed suite(s) de tests ont échoué"
        return 1
    fi
}

# Menu principal
show_menu() {
    echo ""
    echo "Choisissez une option:"
    echo "1) Tests unitaires uniquement"
    echo "2) Tests d'intégration uniquement"
    echo "3) Tests end-to-end uniquement"
    echo "4) Tests de démonstration"
    echo "5) Tests QR Code spécifiques"
    echo "6) Tests d'impression spécifiques"
    echo "7) Tests avec couverture de code"
    echo "8) Tous les tests"
    echo "9) Tests rapides (unitaires + QR Code)"
    echo "0) Quitter"
    echo ""
}

# Gestion des arguments en ligne de commande
case "${1:-}" in
    "unit")
        run_unit_tests
        exit $?
        ;;
    "integration")
        run_integration_tests
        exit $?
        ;;
    "e2e")
        run_e2e_tests
        exit $?
        ;;
    "demo")
        run_demo_tests
        exit $?
        ;;
    "qrcode")
        run_qrcode_tests
        exit $?
        ;;
    "printing")
        run_printing_tests
        exit $?
        ;;
    "coverage")
        run_coverage_tests
        exit $?
        ;;
    "all")
        run_all_tests
        exit $?
        ;;
    "quick")
        print_status "Tests rapides (unitaires + QR Code)..."
        run_unit_tests && run_qrcode_tests
        exit $?
        ;;
    "help" | "-h" | "--help")
        echo "Usage: $0 [option]"
        echo ""
        echo "Options disponibles:"
        echo "  unit          Tests unitaires"
        echo "  integration   Tests d'intégration"
        echo "  e2e           Tests end-to-end"
        echo "  demo          Tests de démonstration"
        echo "  qrcode        Tests QR Code"
        echo "  printing      Tests d'impression"
        echo "  coverage      Tests avec couverture"
        echo "  all           Tous les tests"
        echo "  quick         Tests rapides"
        echo "  help          Afficher cette aide"
        echo ""
        exit 0
        ;;
    "")
        # Mode interactif
        ;;
    *)
        print_error "Option inconnue: $1"
        echo "Utilisez '$0 help' pour voir les options disponibles"
        exit 1
        ;;
esac

# Mode interactif
while true; do
    show_menu
    read -p "Votre choix: " choice
    
    case $choice in
        1)
            run_unit_tests
            ;;
        2)
            run_integration_tests
            ;;
        3)
            run_e2e_tests
            ;;
        4)
            run_demo_tests
            ;;
        5)
            run_qrcode_tests
            ;;
        6)
            run_printing_tests
            ;;
        7)
            run_coverage_tests
            ;;
        8)
            run_all_tests
            ;;
        9)
            print_status "Tests rapides (unitaires + QR Code)..."
            run_unit_tests && run_qrcode_tests
            ;;
        0)
            print_status "Au revoir!"
            exit 0
            ;;
        *)
            print_warning "Option invalide. Veuillez choisir entre 0 et 9."
            ;;
    esac
    
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
done
