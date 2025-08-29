#!/usr/bin/env python3
"""
Test des imports pour vérifier que la configuration fonctionne.
"""

import sys
import os

# Ajout du répertoire racine au PYTHONPATH (même logique que conftest.py)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test que tous les imports critiques fonctionnent."""
    try:
        # Désactiver temporairement l'initialisation de la base
        import os
        os.environ['DISABLE_DB_INIT'] = '1'
        
        # Test import des modèles (sans initialiser l'app)
        import app_acfc.modeles # type: ignore
        print("✅ Import app_acfc.modeles réussi")
        
        # Test import des services
        import app_acfc.services # type: ignore
        print("✅ Import app_acfc.services réussi")
        
        # Test import des habilitations
        import app_acfc.habilitations # type: ignore
        print("✅ Import app_acfc.habilitations réussi")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

if __name__ == "__main__":
    print("Test des imports ACFC...")
    print(f"Python path: {sys.path[:3]}...")  # Affiche les 3 premiers éléments
    print(f"Working directory: {os.getcwd()}")
    
    success = test_imports()
    
    if success:
        print("\n🎉 Tous les imports fonctionnent correctement!")
        sys.exit(0)
    else:
        print("\n💥 Erreurs d'import détectées")
        sys.exit(1)
