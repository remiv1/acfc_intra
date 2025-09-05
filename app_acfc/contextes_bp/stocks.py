from flask import Blueprint, jsonify

stocks_bp = Blueprint('stocks',
                      __name__,
                      url_prefix='/stocks',
                      static_folder='statics/stocks')


@stocks_bp.route('/')
def stocks_index():
    return jsonify({'stocks': []})
