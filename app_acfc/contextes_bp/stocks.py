from flask import Blueprint, jsonify

stocks_bp = Blueprint('stocks',
                      __name__,
                      url_prefix='/stocks',
                      static_folder='statics/stocks')


@stocks_bp.route('/')
def stocks_index():
    return jsonify({'stocks': []})


@stocks_bp.route('/hello')
def hello_stocks():
    return 'Stocks blueprint: hello'
