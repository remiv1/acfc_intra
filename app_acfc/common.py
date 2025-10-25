from weasyprint import HTML
from typing import Optional, Tuple, Any, Dict
import os
import cups
from abc import ABC, abstractmethod

class DocumentHandling(ABC):
    @abstractmethod
    def download(self, *, ref: Any) -> bool:
        pass

    @abstractmethod
    def upload(self, *, ref: Any, rendered_template: str, css_style: str = None) -> bool:
        pass

    def _exists(self) -> bool:
        """Vérifie si un document existe pour un chemin donné."""
        if not os.path.exists(self.file_path) or not self.file_path:
            return False
        return True

    def _generate_pdf_and_upload(self, template: str, css_style: str = None) -> None:
        """
        Générer un PDF à partir d'un modèle donné et l'enregistrer à l'emplacement spécifié.

        Args:
            template (str): Le modèle à utiliser pour générer le PDF.
            css_style (str, optional): Le style CSS à appliquer au PDF.
        Returns:
            str: Le chemin du fichier du PDF généré.
        """
        try:
            HTML(string=template).write_pdf(target=self.file_path, stylesheets=css_style)

        except OSError as e:
            raise OSError("Erreur fichier :", e)
        except Exception as e:
            raise ValueError("Erreur de valeur :", e)
        
        return None

    def print_with_cups(self, *, printer_name: str = None, **kwargs) -> int:
        """
        Imprimer un fichier en utilisant CUPS.
        Args:
            file_path (str): Le chemin du fichier à imprimer.
            printer_name (str, optional): Le nom de l'imprimante. Si None, la première imprimante disponible sera utilisée.
        Returns:
            int: L'ID du travail d'impression.
        """
        if not self.file_path and 'file_path' not in kwargs:
            raise ValueError("Le chemin du fichier ne peut pas être vide.")
        conn = cups.Connection()
        printers = conn.getPrinters()
        if not printer_name:
            printer_name = list(printers.keys())[0]  # Utilise le premier disponible
        job_id = conn.printFile(printer_name, self.file_path, "Document", {})
        return job_id

class AccountingDocument(DocumentHandling):
    def __init__(self, *, type_doc: str):
        """
        Initialise les chemins des dossiers de comptabilité à partir des variables d'environnement.
        Args:
            type_doc (str): Type de document comptable.
                - "balance" pour la balance
                - "g_ledger" pour le grand livre
                - "j_ledger" pour le livre journal
        """
        self.type_doc = type_doc
        match type_doc:
            case "balance":
                self.doc_path = os.getenv("ACC_BALANCE_PATH")
            case "g_ledger":
                self.doc_path = os.getenv("ACC_G_LEDGER_PATH")
            case "j_ledger":
                self.doc_path = os.getenv("ACC_J_LEDGER_PATH")
            case _:
                self.doc_path = os.getenv("ACCOUNTING_PATH")

    def download(self, *, ref: Tuple[int, int]) -> bool:
        """
        Méthode pour télécharger un document comptable basé sur une référence de mois et d'année.
        Args:
            ref (Tuple[int, int]): Un tuple contenant le mois et l'année (mois, année).
            0 pour le mois indique une demande pour l'année complète.
        Returns:
            bool: True si le téléchargement a réussi, sinon une exception est levée.
        """
        month, year = ref

        # Création du chemin en fonction de l'année et du mois
        if month < 0 or month > 12:
            raise ValueError("Mois invalide. Doit être entre 0 et 12.")
        else:
            self.file_path = os.path.join(self.doc_path, f"{year}", f"{month:02d if month > 0 else 'complete_year'}.pdf")

        # Validation de l'existence du document
        if not self._exists(path_document=self.file_path):
            raise FileNotFoundError(f"Document introuvable pour {month}/{year} dans {self.doc_path}")

        # Logique de téléchargement ici
        with open(file=self.file_path, mode="rb") as f:
            return f.read()

        return True

    def upload(self, *, ref: Tuple[int, int], rendered_template: str, css_style: str = None) -> bool:
        """
        Méthode pour téléverser un document comptable basé sur une référence de mois et d'année.
        Args:
            ref (Tuple[int, int]): Un tuple contenant le mois et l'année (mois, année).
            0 pour le mois indique une demande pour l'année complète.
            file (bytes): Le contenu du fichier à téléverser.
        Returns:
            bool: True si le téléversement a réussi, sinon une exception est levée.
        """
        month, year = ref

        # Création du chemin en fonction de l'année et du mois
        if month < 0 or month > 12:
            raise ValueError("Mois invalide. Doit être entre 0 et 12.")
        else:
            self.file_path = os.path.join(self.doc_path, f"{year}", f"{month:02d if month > 0 else 'complete_year'}.pdf")

        # Logique de téléversement ici
        self._generate_pdf_and_upload(template=rendered_template, css_style=css_style)

        return True

class BillsDocument(DocumentHandling):
    def __init__(self):
        """
        Initialise les chemins des dossiers de factures à partir des variables d'environnement.
        """
        self.doc_path = os.getenv("BILLS_PATH")
        self.TEMPLATE = 'orders/bill_print.html'

    def download(self, *, ref: str) -> bytes:
        """
        Méthode pour télécharger une facture basée sur une référence donnée.
        Args:
            ref (str): La référence de la facture à télécharger.
        Returns:
            bool: True si le téléchargement a réussi, sinon une exception est levée.
        """
        # Logique de création du chemin en fonction de la référence
        year = ref.split('-')[0]
        month = ref.split('-')[1]
        self.folder_path = os.path.join(self.doc_path, year, month)
        self.file_path = os.path.join(self.folder_path, f"{ref.replace('-', '')}.pdf")

        # Validation de l'existence du document
        if not self._exists():
            raise FileNotFoundError(f"Facture introuvable pour la référence {ref} dans {self.folder_path}")

        # Logique de téléchargement ici
        with open(file=self.file_path, mode="rb") as f:
            return f.read()

    def upload(self, *, ref: str, rendered_template: str, css_style: str = None) -> bool:
        """
        Méthode pour téléverser une facture basée sur une référence donnée.
        Args:
            ref (str): La référence de la facture à téléverser au format 'YYYY-MM-IIIIII-I'.
            context (Dict[str, Any]): Le contexte à utiliser pour générer le PDF.
            css_style (str, optional): Le style CSS à appliquer au PDF.
        Returns:
            bool: True si le téléversement a réussi, sinon une exception est levée.
        """
        # Logique de création du chemin en fonction de la référence
        year = ref.split('-')[0]
        month = ref.split('-')[1]
        self.folder_path = os.path.join(self.doc_path, year, month)
        try:
            os.makedirs(self.folder_path, exist_ok=True)
        except Exception as e:
            # Gérer l'erreur de création de dossier
            raise OSError(f"Erreur lors de la création du dossier : {e}")

        self.file_path = os.path.join(self.folder_path, f"{ref.replace('-', '')}.pdf")

        # Logique de téléversement ici
        self._generate_pdf_and_upload(template=rendered_template, css_style=css_style)

        return True
    