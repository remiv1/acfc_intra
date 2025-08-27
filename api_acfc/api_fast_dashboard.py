# Exemple de routes pour l'API Fast
# À intégrer dans votre application FastAPI séparée

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

# Router pour les endpoints du dashboard
dashboard_router = APIRouter(prefix="/api/fast", tags=["dashboard"])

@dashboard_router.get("/commandes-en-cours")
async def get_commandes_en_cours() -> Dict[str, Any]:
    """
    Récupère la liste des commandes en cours (non facturées, non envoyées)
    
    Returns:
        Dict contenant la liste des commandes avec leurs détails
    """
    try:
        # Exemple de données - À remplacer par une vraie requête DB
        commandes_exemple: list[Dict[str, Any]] = [
            {
                "id": 1,
                "numero": "CMD-2025-0001",
                "client": "Entreprise ABC",
                "montant": 1250.00,
                "date": "2025-08-20",
                "statut": "en_cours",
                "nb_articles": 5
            },
            {
                "id": 2,
                "numero": "CMD-2025-0002", 
                "client": "Société XYZ",
                "montant": 890.50,
                "date": "2025-08-21",
                "statut": "en_preparation",
                "nb_articles": 3
            },
            {
                "id": 3,
                "numero": "CMD-2025-0003",
                "client": "SARL DEF",
                "montant": 2150.75,
                "date": "2025-08-22",
                "statut": "en_cours",
                "nb_articles": 8
            }
        ]
        
        return {
            "success": True,
            "commandes": commandes_exemple,
            "total_commandes": len(commandes_exemple),
            "total_montant": sum(cmd["montant"] for cmd in commandes_exemple),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des commandes: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@dashboard_router.get("/indicateurs-commerciaux")
async def get_indicateurs_commerciaux() -> Dict[str, Any]:
    """
    Récupère les principaux indicateurs commerciaux
    
    Returns:
        Dict contenant les KPIs commerciaux
    """
    try:
        # Calcul de la période (exemple: mois en cours)
        aujourd_hui = datetime.now()
        debut_mois = aujourd_hui.replace(day=1)
        
        # Exemple de données - À remplacer par de vraies requêtes DB
        indicateurs_exemple: Dict[str, Any] = {
            "ca_mensuel": 45230.75,
            "ca_mensuel_objectif": 50000.00,
            "nb_commandes": 23,
            "nb_commandes_mois_precedent": 19,
            "nb_devis": 12,
            "nb_devis_en_attente": 8,
            "nb_clients": 156,
            "nb_nouveaux_clients": 4,
            "taux_conversion_devis": 67.5,
            "panier_moyen": 1966.99,
            "periode": {
                "debut": debut_mois.isoformat(),
                "fin": aujourd_hui.isoformat(),
                "nom": "Août 2025"
            }
        }
        
        # Calcul de tendances
        indicateurs_exemple["evolution_ca"] = round(
            ((indicateurs_exemple["ca_mensuel"] / indicateurs_exemple["ca_mensuel_objectif"]) - 1) * 100, 1
        )
        
        indicateurs_exemple["evolution_commandes"] = round(
            ((indicateurs_exemple["nb_commandes"] / indicateurs_exemple["nb_commandes_mois_precedent"]) - 1) * 100, 1
        )
        
        return {
            "success": True,
            "indicateurs": indicateurs_exemple,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des indicateurs: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@dashboard_router.get("/activite-recente")
async def get_activite_recente(limit: int = 10) -> Dict[str, Any]:
    """
    Récupère l'activité récente du système
    
    Args:
        limit: Nombre maximum d'éléments à retourner
        
    Returns:
        Dict contenant la liste des activités récentes
    """
    try:
        # Exemple d'activités récentes
        activites_exemple: List[Dict[str, Any]] = [
            {
                "id": 1,
                "type": "commande",
                "action": "création",
                "description": "Nouvelle commande CMD-2025-0003 créée",
                "utilisateur": "jean.dupont",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat()
            },
            {
                "id": 2,
                "type": "client",
                "action": "modification",
                "description": "Client Entreprise ABC modifié",
                "utilisateur": "marie.martin",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
            },
            {
                "id": 3,
                "type": "produit",
                "action": "création",
                "description": "Nouveau produit PROD-789 ajouté au catalogue",
                "utilisateur": "pierre.bernard",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return {
            "success": True,
            "activites": activites_exemple[:limit],
            "total": len(activites_exemple),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'activité: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


# Configuration pour intégrer ce router dans votre app FastAPI principale
