from flask import Blueprint, jsonify
from app_acfc.habilitations import (
    validate_habilitation, ADMINISTRATEUR
    )

admin_bp = Blueprint('admin',
                     __name__,
                     url_prefix='/admin',
                     static_folder='statics/admin')

@validate_habilitation(ADMINISTRATEUR)
@admin_bp.route('/')
def admin_list():
    return jsonify({'admins': []})

@validate_habilitation(ADMINISTRATEUR)
@admin_bp.route('/hello')
def admin_hello():
    return 'Admin blueprint: hello'
