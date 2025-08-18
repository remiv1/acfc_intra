#!/bin/bash
# Script de lancement local pour générer un rapport de suivi

set -e  # Arrêt en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Générateur de Rapport de Suivi - ACFC${NC}"
echo "=================================================="

# Vérifications préalables
echo -e "${YELLOW}🔍 Vérifications préalables...${NC}"

# Vérifier si on est dans un dépôt Git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Erreur: Ce n'est pas un dépôt Git${NC}"
    exit 1
fi

# Vérifier si Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Erreur: Python 3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier si le script existe
if [ ! -f "scripts/generate_progress_report.py" ]; then
    echo -e "${RED}❌ Erreur: Script scripts/generate_progress_report.py introuvable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Vérifications réussies${NC}"

# Paramètres par défaut
DAYS=7
OUTPUT=""
REPO="."

# Traitement des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --days DAYS     Nombre de jours à analyser (défaut: 7)"
            echo "  -o, --output FILE   Fichier de sortie (défaut: auto-généré)"
            echo "  -r, --repo PATH     Chemin vers le dépôt Git (défaut: .)"
            echo "  -h, --help          Affiche cette aide"
            echo ""
            echo "Exemples:"
            echo "  $0                           # Rapport des 7 derniers jours"
            echo "  $0 --days 30                # Rapport des 30 derniers jours"
            echo "  $0 --days 7 --output mon_rapport.md"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Option inconnue: $1${NC}"
            echo "Utilisez --help pour voir les options disponibles"
            exit 1
            ;;
    esac
done

# Affichage des paramètres
echo ""
echo -e "${BLUE}📊 Paramètres de génération:${NC}"
echo "  📅 Période: $DAYS derniers jours"
echo "  📁 Dépôt: $REPO"
if [ -n "$OUTPUT" ]; then
    echo "  📄 Sortie: $OUTPUT"
else
    echo "  📄 Sortie: Auto-générée"
fi

# Génération du rapport
echo ""
echo -e "${YELLOW}🔄 Génération du rapport en cours...${NC}"

# Construction de la commande
CMD="python3 scripts/generate_progress_report.py --days $DAYS --repo $REPO"
if [ -n "$OUTPUT" ]; then
    CMD="$CMD --output $OUTPUT"
fi

# Exécution
if eval $CMD; then
    echo -e "${GREEN}✅ Rapport généré avec succès!${NC}"
    
    # Affichage du fichier de sortie
    if [ -n "$OUTPUT" ]; then
        GENERATED_FILE="$OUTPUT"
    else
        GENERATED_FILE="suivi_realisation_auto_$(date +%Y%m%d).md"
    fi
    
    if [ -f "$GENERATED_FILE" ]; then
        echo -e "${BLUE}📄 Fichier créé: $GENERATED_FILE${NC}"
        
        # Affichage de quelques statistiques
        LINES=$(wc -l < "$GENERATED_FILE")
        SIZE=$(du -h "$GENERATED_FILE" | cut -f1)
        echo -e "${BLUE}📏 Taille: $LINES lignes, $SIZE${NC}"
        
        # Proposition d'ouverture
        echo ""
        echo -e "${YELLOW}💡 Suggestions:${NC}"
        echo "  • Ouvrir le fichier: code '$GENERATED_FILE'"
        echo "  • Voir un aperçu: head -20 '$GENERATED_FILE'"
        echo "  • Ajouter au Git: git add '$GENERATED_FILE'"
        
    else
        echo -e "${RED}❌ Fichier de sortie non trouvé${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Échec de la génération du rapport${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Processus terminé avec succès!${NC}"
