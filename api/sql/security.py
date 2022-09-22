import os
from . import db_interface
from hexo_circle_of_friends.models import Secert


def get_secert_key():
    # random secert key
    session = db_interface.db_init()
    secert = session.query(Secert).all()
    if len(secert) == 1:
        secert_key = secert[0].secert_key
    else:
        secert_key = str(os.urandom(16).hex())
        tb_obj = Secert(secert_key=secert_key)
        session.add(tb_obj)
    session.commit()
    session.close()
    return secert_key
