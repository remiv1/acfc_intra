from flask import Blueprint, jsonify

commercial_bp = Blueprint('commercial',
                          __name__,
                          url_prefix='/commercial',
                          static_folder='statics/commercial')


@commercial_bp.route('/')
def commercial_index():
    return jsonify({'offers': []})


@commercial_bp.route('/hello')
def hello_commercial():
    return 'Commercial blueprint: hello'
