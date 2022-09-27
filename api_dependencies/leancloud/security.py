import os
import leancloud
from leancloud.errors import LeanCloudError
from . import db_interface


async def get_secret_key():
    # random secret key
    db_interface.db_init()

    secret = leancloud.Object.extend('secret')
    secret_db = secret()
    query = secret.query
    query.limit(10)
    try:
        query.select('secret_key')
        secret_key = query.first().get("secret_key")
    except LeanCloudError as e:
        secret_key = str(os.urandom(16).hex())
        # 表不存在
        secret_db.set("secret_key", secret_key)
        secret_db.save()

    return secret_key
