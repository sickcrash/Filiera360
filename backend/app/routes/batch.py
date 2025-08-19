from flask import Blueprint
from ..controller.batch_controller import get_batch_controller, get_batch_history_controller, \
    upload_batch_controller, update_batch_controller

batch_bp = Blueprint('batch', __name__)

batch_bp.route('/getBatch', methods=['GET'])(get_batch_controller)
batch_bp.route('/getBatchHistory', methods=['GET'])(get_batch_history_controller)
batch_bp.route('/uploadBatch', methods=['POST'])(upload_batch_controller)
batch_bp.route('/updateBatch', methods=['POST'])(update_batch_controller)

