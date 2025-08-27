from flask import Blueprint, jsonify

catalogue_bp = Blueprint('catalogue',
                         __name__,
                         url_prefix='/catalogue',
                         static_folder='statics/catalogue')


@catalogue_bp.route('/')
def catalogue_list():
    return jsonify({'products': []})


@catalogue_bp.route('/hello')
def hello_catalogue():
    return 'Catalogue blueprint: hello'
