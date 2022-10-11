import os
from . import db_interface
from hexo_circle_of_friends.models import Secret
from api_dependencies.utils.vercel_interface import get_env, create_or_update_env
from api_dependencies import tools


async def get_secret_key():
    # random secret key
    if tools.is_vercel_sqlite():
        # vercel+sqlite特殊处理，secret_key读取和保存在vercel中
        secret_key = str(os.urandom(16).hex())
        # 获取vercel_access_token
        vercel_acces_token = os.environ["VERCEL_ACCESS_TOKEN"]
        project_name = "hexo-circle-of-friends"
        env_name = "SECRET_KEY"
        env_value = secret_key
        res = await get_env(vercel_acces_token, project_name, env_name)
        if res:
            secret_key = res.get("value")
        else:
            await create_or_update_env(vercel_acces_token, project_name, env_name, env_value)
    else:
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
