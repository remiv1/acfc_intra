from sqlalchemy.orm import Session as SessionBdDType
from app_acfc.modeles import Catalogue, get_db_session
from typing import List

class ProductsModel:
    """
    Modèle pour gérer les produits du catalogue
    Attributes:
        catalogue (List[Catalogue]): Liste de tous les produits du catalogue
        product (Catalogue): Produit spécifique
        millesimes (List[int]): Liste des millésimes distincts
        product_types (List[str]): Liste des types de produits distincts
        geo_areas (List[str]): Liste des zones géographiques distinctes
    """
    def __init__(self):
        """Initialise le modèle des produits"""
        self.catalogue: List[Catalogue] = []
        self.product: Catalogue
        self.millesimes: List[int] = []
        self.product_types: List[str] = []
        self.geo_areas: List[str] = []

    def get_product_by_ref(self, reference: str) -> 'ProductsModel':
        """
        Récupère un produit par sa référence
        args:
            reference (str): Référence du produit
        Returns:
            ProductsModel: Instance de ProductsModel contenant le produit
        """
        session_db: SessionBdDType = get_db_session()
        product = session_db.query(Catalogue) \
            .filter(Catalogue.reference == reference) \
            .first()
        not_products: List[Catalogue] = []
        self.product = product if product else not_products
        return self
    
    def get_all_products(self) -> 'ProductsModel':
        """
        Récupère tous les produits du catalogue
        Returns:
            ProductsModel: Instance de ProductsModel contenant la liste des produits
        """
        session_db: SessionBdDType = get_db_session()
        catalogue = session_db.query(Catalogue).all()
        not_catalogue: List[Catalogue] = []
        self.catalogue = catalogue if catalogue else not_catalogue
        return self
    
    def get_context_catalogue(self) -> 'ProductsModel':
        """
        Récupère les millésimes, catégories et types de produits pour le contexte
        Returns:
            ProductsModel: Instance de ProductsModel contenant le catalogue et les filtres
        """
        session_db: SessionBdDType = get_db_session()
        # Récupération des millésimes distincts pour le filtre
        millesimes = session_db.query(Catalogue.millesime) \
                            .distinct() \
                            .filter(Catalogue.millesime.isnot(None)) \
                            .order_by(Catalogue.millesime.desc()) \
                            .all()
        self.millesimes = [m[0] for m in millesimes if m[0]]
        # Récupération des types de produits distincts pour le filtre
        product_types = session_db.query(Catalogue.type_produit) \
                            .distinct() \
                            .filter(Catalogue.type_produit.isnot(None)) \
                            .order_by(Catalogue.type_produit) \
                            .all()
        self.product_types = [p[0] for p in product_types if p[0]]
        # Récupération des zones géographiques distinctes pour le filtre
        geo_areas = session_db.query(Catalogue.geographie) \
                            .distinct() \
                            .filter(Catalogue.geographie.isnot(None)) \
                            .order_by(Catalogue.geographie) \
                            .all()
        self.geo_areas = [g[0] for g in geo_areas if g[0]]
        return self
