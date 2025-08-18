from flask import Flask, Response, render_template
from waitress import serve

# Create the Flask app
acfc = Flask(__name__,
             static_folder='statics',
             template_folder='templates')

@acfc.before_request
def before_request() -> None:
    print("Before request")

@acfc.after_request
def after_request(response: Response) -> Response:
    print("After request")
    return response

@acfc.route('/')
def index() -> str:
    return render_template('base.html', title='ACFC - Accueil', context='clients')

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


for bp in (clients_bp, catalogue_bp, commercial_bp, comptabilite_bp, stocks_bp):
    acfc.register_blueprint(bp)


if __name__ == '__main__':
    serve(acfc, host="0.0.0.0", port=5000)
