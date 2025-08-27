from flask import Blueprint, jsonify

admin_bp = Blueprint('admin',
                     __name__,
                     url_prefix='/admin',
                     static_folder='statics/admin')


@admin_bp.route('/')
def admin_list():
    return jsonify({'admins': []})


@admin_bp.route('/hello')
def admin_hello():
    return 'Admin blueprint: hello'
