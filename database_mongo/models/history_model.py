from bson import ObjectId
from datetime import datetime, UTC

def create_history_model(blockchain_product_id, modified_by, changes):
    return {
        "blockchainProductId": blockchain_product_id,
        "modifiedBy": ObjectId(modified_by),
        "timestamp": datetime.now(UTC),
        # lista di dizionari: [{field, oldValue, newValue}, ...]
        "changes": changes
    }