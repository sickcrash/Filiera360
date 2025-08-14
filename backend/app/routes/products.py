from flask import Blueprint
from ..controller.products_controller import get_product, get_product_history

products_bp = Blueprint('products', __name__)

products_bp.route('/getProduct', methods=['GET'])(get_product)
products_bp.route('/getProductHistory', methods=['GET'])(get_product_history)
# products_bp.route('/uploadProduct', methods=['POST'])(upload_product)