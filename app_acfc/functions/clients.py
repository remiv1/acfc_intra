"""Module des fonctions utilitaires pour la gestion des clients."""

from datetime import datetime
from typing import Tuple
from flask import Request
from sqlalchemy.orm import Session as SessionBdDType
from app_acfc.db_models import Client, Part, Pro

# ================================================================
# FONCTIONS HORS ROUTES
# ================================================================

def validate_mail(email: str | None) -> Tuple[bool, str]:
    """
    Valide le format d'une adresse email.

    Args:
        email (str): Adresse email à valider

    Returns:
        bool: True si l'email est valide, False sinon
        str: Message d'erreur si invalide, chaîne vide sinon
    """
    if not email:
        return False, "missing"
    elif '@' in email and '.' in email.split('@')[-1]:
        return True, ""
    return False, "invalid"

# ================================================================
# CLASSES HORS ROUTES
# ================================================================

class ClientMethods:
    """
    Classe utilitaire pour les méthodes liées aux clients.

    Methodes statiques pour :
        - Récupération du taux de réduction
        - Création/modification de clients particuliers ou professionnels
    """

    @staticmethod
    def get_reduces(http_request: Request) -> float:
        """
        Récupère le taux de réduction depuis la requête.

        Args:
            http_request (Request): Objet de requête Flask

        Returns:
            float: Taux de réduction (0.10 par défaut si non spécifié)
        """
        reduces_str = http_request.form.get('reduces', '0.10')
        try:
            return float(reduces_str) / 100  # Conversion pourcentage vers décimal
        except (ValueError, TypeError):
            return 10.0  # Valeur par défaut : 10%

    @staticmethod
    def create_or_modify_client(http_request: Request, type_client: int, client: Client,
                                db_session: SessionBdDType, type_test: str = 'create') -> None:
        '''
        Teste la création d'un client particulier ou professionnel.
        Création du client suivant le type.
        '''
        if type_client == 1:  # Particulier
            ClientMethods.create_or_modify_part(http_request, client, db_session, type_test)

        elif type_client == 2:  # Professionnel
            ClientMethods.create_or_modify_pro(http_request, client, db_session, type_test)

    @staticmethod
    def create_or_modify_part(http_request: Request, client: Client, db_session: SessionBdDType,
                              type_test: str = 'create') -> None:
        """
        Crée ou modifie un client particulier.

        Args:
            http_request (Request): Objet de requête Flask
            client (Client): Objet client à modifier ou à créer
            db_session (SessionBdDType): Session de base de données
            type_test (str): Type de test ('create' ou 'update')
        """
        # Récupération des données spécifiques au particulier depuis le formulaire
        prenom = http_request.form.get('prenom', '')
        nom = http_request.form.get('nom', '')
        date_naissance_str = http_request.form.get('date_naissance', None)
        lieu_naissance = http_request.form.get('lieu_naissance', '')

        # Création ou récupération du client particulier
        part = Part(id_client=client.id) if type_test == 'create' else client.part
        part.prenom = prenom
        part.nom = nom
        part.date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date() \
                                    if date_naissance_str else None
        part.lieu_naissance = lieu_naissance if lieu_naissance else None

        if type_test == 'create':
            db_session.add(part)
        else:
            db_session.merge(part)

    @staticmethod
    def create_or_modify_pro(http_request: Request, client: Client,
                             db_session: SessionBdDType, type_test: str = 'create') -> None:
        """
        Crée ou modifie un client professionnel.

        Args:
            http_request (Request): Objet de requête Flask
            client (Client): Objet client à modifier ou à créer
            db_session (SessionBdDType): Session de base de données
            type_test (str): Type de test ('create' ou 'update')
        """
        # Récupération des données spécifiques au professionnel depuis le formulaire
        raison_sociale = http_request.form.get('raison_sociale', '')
        type_pro_str = http_request.form.get('type_pro', '')
        siren = http_request.form.get('siren', '')
        rna = http_request.form.get('rna', '')

        # Création ou récupération du client professionnel
        pro = Pro(id_client=client.id) if type_test == 'create' else client.pro
        pro.raison_sociale = raison_sociale
        pro.type_pro = int(type_pro_str)
        pro.siren = siren if siren else None
        pro.rna = rna if rna else None

        if type_test == 'create':
            db_session.add(pro)
        else:
            db_session.merge(pro)
