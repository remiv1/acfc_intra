"""Module des fonctions utilitaires pour la gestion des clients."""

from datetime import datetime
from typing import Tuple, List, Any
from flask import Request
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload, Session as SessionBdDType, aliased
from app_acfc.db_models import Client, Part, Pro, Telephone, Mail, Adresse

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

class ClientsAPI:
    """
    Classe de gestion des filtres pour l'API de recherche de clients.
    """
    def __init__(self, req:Request, session: SessionBdDType):
        self.request = req
        self.type_client = req.args.get('type_client', type=int)
        self.has_phone = req.args.get('has_phone', type=int)
        self.has_email = req.args.get('has_email', type=int)
        self.departement = req.args.get('departement', '').strip()
        self.ville = req.args.get('ville', '').strip()
        self.is_active = req.args.get('is_active', type=int)
        self.search = req.args.get('search', '').strip()
        self.limit = req.args.get('limit', default=100, type=int)
        self.offset = req.args.get('offset', default=0, type=int)
        self.session = session
        self.part_alias = aliased(Part)
        self.pro_alias = aliased(Pro)
        self.joined_tables: set[str] = set()
        self.query = self.session.query(Client)
        self._search_conditions: List[Any] = []

    def close_session(self):
        """Ferme la session de base de données si elle existe."""
        if self.session:
            self.session.close()

    def _validate_limit(self):
        """Valide et ajuste la limite des résultats."""
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 500:
            self.limit = 500

    def _validate_offset(self):
        """Valide et ajuste l'offset des résultats."""
        if self.offset < 0:
            self.offset = 0

    def filter_part_pro(self):
        """Filtre par type de client (Particulier/Professionnel)."""
        self.add_joins()
        if self.type_client in [1, 2]:
            self.query = self.query.filter(Client.type_client == self.type_client)
        return self

    def filter_has_phone(self):
        """Filtre par présence de téléphone."""
        if self.has_phone is not None:
            self.add_joins()
            if self.has_phone == 1:
                self.query = self.query.join(Telephone).filter(Telephone.id_client == Client.id)
            else:
                subquery = self.session.query(Telephone.id_client).distinct()
                self.query = self.query.filter(~Client.id.in_(subquery))
        return self

    def filter_has_email(self):
        """Filtre par présence d'email."""
        if self.has_email is not None:
            self.add_joins()
            if self.has_email == 1:
                self.query = self.query.join(Mail).filter(Mail.id_client == Client.id)
            else:
                subquery = self.session.query(Mail.id_client).distinct()
                self.query = self.query.filter(~Client.id.in_(subquery))
        return self

    def filter_by_dpt(self):
        """Filtre par département (code postal)."""
        self.add_joins()
        if self.departement:
            self.query = self.query.join(Adresse) \
                            .filter(Adresse.id_client == Client.id,
                                    Adresse.is_inactive == False,   # pylint: disable=singleton-comparison
                                    Adresse.code_postal.ilike(f"%{self.departement}%"))
        return self

    def filter_by_town(self):
        """Filtre par ville."""
        self.add_joins()
        if self.ville:
            self.query = self.query.join(Adresse) \
                             .filter(Adresse.id_client == Client.id,    #pylint: disable=singleton-comparison
                                     Adresse.is_inactive == False,  # pylint: disable=singleton-comparison
                                     Adresse.ville.ilike(f"%{self.ville}%"))
        return self

    def add_joins(self):
        """Ajoute les jointures nécessaires à la requête."""
        if 'part' not in self.joined_tables:
            self.query = self.query.outerjoin(self.part_alias)
            self.joined_tables.add('part')

        if 'pro' not in self.joined_tables:
            self.query = self.query.outerjoin(self.pro_alias)
            self.joined_tables.add('pro')

        if 'adresse' not in self.joined_tables:
            self.query = self.query.outerjoin(Adresse)
            self.joined_tables.add('adresse')

        if 'telephone' not in self.joined_tables:
            self.query = self.query.outerjoin(Telephone)
            self.joined_tables.add('telephone')

        if 'email' not in self.joined_tables:
            self.query = self.query.outerjoin(Mail)
            self.joined_tables.add('email')

    def filter_textual_search(self):
        """Filtre par recherche textuelle libre."""
        # Filtrage par recherche textuelle
        if self.search:
            # Pour les particuliers, recherche par nom et prénom
            # Pour les professionnels, recherche par raison sociale

            if self.type_client != 2:
                self._search_conditions \
                    .append(and_(Client.type_client == 1,
                                 or_(self.part_alias.prenom.ilike(f"%{self.search}%"),
                                     self.part_alias.nom.ilike(f"%{self.search}%"))))

            if self.type_client != 1:
                self._search_conditions \
                    .append(and_(Client.type_client == 2,
                                 or_(self.pro_alias.raison_sociale.ilike(f"%{self.search}%"),
                                     self.pro_alias.siren.ilike(f"%{self.search}%"))))

            if self._search_conditions:
                self.add_joins()
                self.query = self.query.filter(or_(*self._search_conditions))

            # Tri par nom d'affichage
            self.query = self.query \
                        .order_by(
                        func.coalesce(
                        func.concat(self.part_alias.prenom,' ', self.part_alias.nom),  # pylint: disable=not-callable
                        func.concat(self.pro_alias.raison_sociale, ' ', self.pro_alias.siren)))    # pylint: disable=not-callable

        return self

    def get_query(self):
        """Prépare la requête initiale avec les options de chargement."""
        self._validate_limit()
        self._validate_offset()
        self.query = self.session.query(Client).options(
            joinedload(Client.part),
            joinedload(Client.pro),
            joinedload(Client.tels),
            joinedload(Client.mails),
            joinedload(Client.adresses)
        )
        return self
