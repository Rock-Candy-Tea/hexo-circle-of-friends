from . import db_interface
from hexo_circle_of_friends.models import Config



# def get_token(token: str = Depends(jwt.oauth2_scheme)):
#     session = db_interface.db_init()
#     config = session.query(Config).all()
#     if len(config) == 1:
#         pass
#     else:
#         return None
