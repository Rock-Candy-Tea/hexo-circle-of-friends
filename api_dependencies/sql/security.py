import os
from . import db_interface
from hexo_circle_of_friends.models import Secret


def get_secret_key():
    # random secret key
    session = db_interface.db_init()
    secret = session.query(Secret).all()
    if len(secret) == 1:
        secret_key = secret[0].secret_key
    else:
        secret_key = str(os.urandom(16).hex())
        tb_obj = Secret(secret_key=secret_key)
        session.add(tb_obj)
    session.commit()
    session.close()
    return secret_key
