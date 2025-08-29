#!/usr/bin/env python3
"""
Test simple pour le formulaire de création/modification de client.
Ce script valide la syntaxe et les imports du module clients.
"""

import sys
import os
from flask import Blueprint
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from typing import List, Any

def test_client_module_import():
    """Test d'import du module clients."""
    try:
        from app_acfc.contextes_bp.clients import clients_bp    # type: ignore
        print("✅ Import du module clients réussi")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import du module clients : {e}")
        return False

def test_client_routes():
    """Test de la présence des routes."""
    try:
        from app_acfc.contextes_bp.clients import clients_bp
        
        # Annotation de type pour clients_bp
        clients_bp: Blueprint

        # Récupération des routes
        routes: List[str] = []
        for rule in clients_bp.url_map.iter_rules():    # type: ignore
            routes.append(f"{rule.rule} -> {rule.endpoint}")    # type: ignore
        
        print("📋 Routes détectées :")
        for route in routes:
            print(f"   {route}")
        
        print("\n✅ Test des routes terminé")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test des routes : {e}")
        return False

def test_template_exists():
    """Test de l'existence du template."""
    template_path = "app_acfc/templates/clients/client_form.html"
    if os.path.exists(template_path):
        print("✅ Template client_form.html trouvé")
        return True
    else:
        print("❌ Template client_form.html introuvable")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test du formulaire client ACFC")
    print("=" * 50)
    
    tests = [
        test_client_module_import,
        test_client_routes,
        test_template_exists
    ]
    
    results: List[Any] = []
    for test in tests:
        print(f"\n🔍 Exécution de {test.__name__}...")
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 Tous les tests réussis ({success_count}/{total_count})")
        return 0
    else:
        print(f"⚠️  Tests partiellement réussis ({success_count}/{total_count})")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
