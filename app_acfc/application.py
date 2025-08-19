from flask import Flask, Response, render_template, request, session, Blueprint
from waitress import serve
from typing import Any, Dict, Tuple
from werkzeug.exceptions import HTTPException
from password_service import PasswordService

# Create the Flask app
acfc = Flask(__name__,
             static_folder='statics',
             template_folder='templates')

# Création des constantes pour la maintenabilité
BASE: str = 'base.html'
LOGIN: Dict[str, str] = {
    'title': 'ACFC - Login',
    'context': 'login',
    'page': BASE
}
CLIENT: Dict[str, str] = {
    'title': 'ACFC - Clients',
    'context': 'clients',
    'page': BASE
}
ph_acfc = PasswordService()

@acfc.before_request
def before_request() -> str | None:
    if not session:
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'])

@acfc.after_request
def after_request(response: Response) -> Response:
    print("After request")
    return response

@acfc.route('/')
def index() -> str:
    return render_template(CLIENT['page'], title=CLIENT['title'], context=CLIENT['context'])

@acfc.route('/login', methods=['GET', 'POST'])
def login() -> Any:
    #TODO : Création d'une route d'authentification

    # Authentification en cas de demande de connexion (POST)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        _return = ph_acfc.verify_password(password, user.password)

    # Affichage de la page de connexion en cas de méthode GET
    elif request.method == 'GET':
        return render_template(BASE, title=LOGIN['title'], context=LOGIN['context'])
    
    # Retour d'erreur 400 dans les autres cas
    else:
        return render_template(BASE, title=LOGIN['title'], context='400')

@acfc.route('/users', methods=['GET', 'POST'])
def users() -> Any:
    #TODO : Création d'une route de création/modification d'utilisateurs
    if request.method == 'POST':
        # Handle user creation logic here
        pass
    #TODO : Création d'une route de récupération d'utilisateurs
    elif request.method == 'GET':
        return render_template(BASE, title='ACFC - Users', context='users')
    else:
        return render_template(BASE, title='ACFC - Users', context='400')

# Import and register other blueprints
try:
    # prefer absolute import when package is installed or run as module
    from app_acfc.contextes_bp.clients import clients_bp
    from app_acfc.contextes_bp.catalogue import catalogue_bp
    from app_acfc.contextes_bp.commercial import commercial_bp
    from app_acfc.contextes_bp.comptabilite import comptabilite_bp
    from app_acfc.contextes_bp.stocks import stocks_bp
except Exception:
    # fallback to local imports when running files directly
    from contextes_bp.clients import clients_bp
    from contextes_bp.catalogue import catalogue_bp
    from contextes_bp.commercial import commercial_bp
    from contextes_bp.comptabilite import comptabilite_bp
    from contextes_bp.stocks import stocks_bp

# Création du tuple des blueprints
acfc_blueprints: Tuple[Blueprint, ...] = (clients_bp, catalogue_bp, commercial_bp, comptabilite_bp, stocks_bp)

# Custom error handlers
@acfc.errorhandler(400)
@acfc.errorhandler(401)
@acfc.errorhandler(403)
@acfc.errorhandler(404)
def handle_4xx_errors(error: HTTPException) -> str:
    return render_template(BASE, title='ACFC - Erreur 4xx', context='400', status_code=error.code, status_message=error.name)

@acfc.errorhandler(500)
@acfc.errorhandler(502)
@acfc.errorhandler(503)
@acfc.errorhandler(504)
def handle_5xx_errors(error: HTTPException) -> str:
    return render_template(BASE, title='ACFC - Erreur 5xx', context='500', status_code=error.code, status_message=error.name)

for bp in acfc_blueprints:
    acfc.register_blueprint(bp)


if __name__ == '__main__':
    serve(acfc, host="0.0.0.0", port=5000)
