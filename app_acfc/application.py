from flask import Flask, Response, render_template, request, Blueprint, session
from flask_session import Session
from waitress import serve
from typing import Any, Dict, Tuple
from werkzeug.exceptions import HTTPException
from services import PasswordService, SecureSessionService
from modeles import SessionBdD, User

# Create the Flask app
acfc = Flask(__name__,
             static_folder='statics',
             template_folder='templates')


# Importer et enregistrer les autres blueprints
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

SecureSessionService(acfc)
Session(acfc)

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
USER: Dict[str, str] = {
    'title': 'ACFC - Utilisateurs',
    'context': 'user',
    'page': BASE
}
INVALID: str = 'Identifiants invalides.'
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

    def _get_credentials() -> Tuple[str, str]:
        return request.form.get('username', ''), request.form.get('password', '')

    def _render_login() -> str:
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'])

    def _apply_successful_login(user: User) -> None:
        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['role'] = user.role
        user.nb_errors = 0

    # Accès à la page de connexion (GET)
    if request.method == 'GET':
        return _render_login()
    elif request.method != 'POST':
        return render_template(BASE, title=LOGIN['title'], context='400')

    # Passage sur la méthode POST (authentification)
    username, password = _get_credentials()
    db_session = SessionBdD()
    user = db_session.query(User).filter_by(username=username).first()

    if not user:
        return render_template(BASE, title=LOGIN['title'], context=LOGIN['context'], message=INVALID)

    if not ph_acfc.verify_password(password, user.sha_mdp):
        user.nb_errors += 1
        try:
            db_session.commit()
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=INVALID)
        except Exception as e:
            db_session.rollback()
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=str(e))

    _apply_successful_login(user)
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        return render_template(BASE, title=LOGIN['title'], context='500', message=str(e))
    # TODO: Vérifier si le mot de passe est noté comme devant être modifié
    if user.is_chg_mdp:
        return render_template(BASE, title=LOGIN['title'], context='change_password', message="Veuillez changer votre mot de passe.")
    return render_template(CLIENT['page'], title=CLIENT['title'], context=CLIENT['context'])


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
