from weasyprint import HTML

def generate_pdf(template: str, path: str, css_style: str = None) -> None:
    """
    Générer un PDF à partir d'un modèle donné et l'enregistrer à l'emplacement spécifié.

    Args:
        template (str): Le modèle à utiliser pour générer le PDF.
        path (str): Le chemin du fichier où le PDF sera enregistré.
        download (bool): Si True, le PDF sera préparé pour le téléchargement.

    Returns:
        str: Le chemin du fichier du PDF généré.
    """
    try:

        HTML(string=template).write_pdf(path, stylesheets=css_style)

    except OSError as e:
        raise OSError("Erreur fichier :", e)
    except Exception as e:
        raise ValueError("Erreur de valeur :", e)
    
    return None