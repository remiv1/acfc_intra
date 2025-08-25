'''
ACFC - Définition des niveaux d'habilitation
=============================================

Module de l'application ACFC (Accounting, Customer Relationship Management, 
Billing & Stock Management) pour documenter les niveaux d'habilitation.
Cette application web d'entreprise fournit une solution intégrée pour la gestion.
Les niveaux d'habilitation sont les suivants :
- Administrateur (1)
- Gestionnaire (2)
- Clients (3)
- Comptabilité (4)
- Ressources Humaines (5)
- Développement IT (6)
- Force de vente (7)

Architecture : Flask + SQLAlchemy + MariaDB + MongoDB (logs)
Serveur WSGI : Waitress (production-ready)
Authentification : Sessions sécurisées avec hachage Argon2

Auteur : ACFC Development Team
Version : 1.0
'''
from functools import wraps
from typing import Callable, Any
from flask import session

# Définition des niveaux d'habilitation
ADMINISTRATEUR = '1'
GESTIONNAIRE = '2'
CLIENTS = '3'
COMPTABILITE = '4'
RESSOURCES_HUMAINES = '5'
DEVELOPPEMENT_IT = '6'
FORCE_DE_VENTE = '7'

def validate_habilitation(required_habilitation: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Décorateur pour valider si l'utilisateur connecté possède une habilitation spécifique.

    Args:
        required_habilitation (str): Habilitation requise (ex: '3').

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: La fonction décorée ou une réponse d'erreur si l'habilitation est manquante.
    """
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Vérifie si l'utilisateur est connecté et possède une habilitation
            habilitations = session.get('habilitations', '')  # Exemple : '1,2,3'
            if required_habilitation not in habilitations:
                raise PermissionError("Accès refusé. Habilitation insuffisante.")
            return function(*args, **kwargs)
        return wrapper
    return decorator
