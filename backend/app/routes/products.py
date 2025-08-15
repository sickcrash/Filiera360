from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controller.products_controller import get_product_controller, get_product_history_controller, \
    upload_product_controller, update_product_controller, like_product_controller, unlike_product_controller, \
    get_liked_products_controller

products_bp = Blueprint('products', __name__)

products_bp.route('/getProduct', methods=['GET'])(get_product_controller)
products_bp.route('/getProductHistory', methods=['GET'])(get_product_history_controller)
products_bp.route('/uploadProduct', methods=['POST'])(jwt_required()(upload_product_controller))
products_bp.route('/updateProduct', methods=['POST'])(jwt_required()(update_product_controller))
products_bp.route('/likeProduct', methods=['POST', 'OPTIONS'])(jwt_required()(like_product_controller))
products_bp.route('/unlikeProduct', methods=['DELETE'])(jwt_required()(unlike_product_controller))
products_bp.route('/getLikedProducts', methods=['GET'])(jwt_required()(get_liked_products_controller))