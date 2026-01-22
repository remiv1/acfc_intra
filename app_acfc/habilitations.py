"""
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
"""
from functools import wraps
from typing import Callable, Any, List
from flask import session, g
from app_acfc.models.templates_models import PrepareTemplates

# Définition des niveaux d'habilitation
ADMINISTRATEUR = '1'
GESTIONNAIRE = '2'
CLIENTS = '3'
COMPTABILITE = '4'
RESSOURCES_HUMAINES = '5'
DEVELOPPEMENT_IT = '6'
FORCE_DE_VENTE = '7'

def validate_habilitation(required_habilitation: List[str] | str,
                          _and: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Décorateur pour valider si l'utilisateur connecté possède une habilitation spécifique.

    Args:
        required_habilitation (str): Habilitation requise (ex: '3') : un seul caractère.
        Utiliser les constantes définies ci-dessus pour plus de clarté.
        _and (bool): Si True, toutes les habilitations dans la liste doivent être présentes

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: La fonction décorée ou une réponse
        d'erreur si l'habilitation est manquante.
    """
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Si l'habilitation a déjà été validée dans cette requête, on passe directement
            if getattr(g, 'habilitation_validated', False):
                return function(*args, **kwargs)
            # Vérifie si l'utilisateur est connecté et possède une habilitation
            habilitations = session.get("habilitations", "")
            is_habilited = False
            if isinstance(required_habilitation, list):
                if _and:
                    is_habilited = all(habilitation in habilitations
                                       for habilitation in required_habilitation)
                else:
                    is_habilited = any(habilitation in habilitations
                                       for habilitation in required_habilitation)
            else:
                is_habilited = required_habilitation in habilitations
            if not is_habilited:
                message = f'Accès refusé. Habilitation requise : {required_habilitation}.' \
                    + f'\nHabilitation actuelle : {session.get("habilitations", "inconnu")}.' \
                    + f'\nUtilisateur : {session.get("pseudo", "Anonyme")}.'
                return PrepareTemplates.error_4xx(status_code=403, status_message=message, log=True)
            g.habilitation_validated = True
            return function(*args, **kwargs)
        return wrapper
    return decorator
