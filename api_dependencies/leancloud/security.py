import os
from . import db_interface


async def get_secret_key():
    # random secret key
    db_interface.db_init()
    secret_db_collection = session.Secret
    document_num = secret_db_collection.count_documents({})
    if document_num == 1:
        secret_key = secret_db_collection.find_one({})["secret_key"]
    else:
        secret_key = str(os.urandom(16).hex())
        secret_db_collection.insert_one({"secret_key": secret_key})

    return secret_key
