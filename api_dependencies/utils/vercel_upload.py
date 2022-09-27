# -*- coding:utf-8 -*-
# Author：yyyz
from typing import Union
import aiohttp


async def get_env(vercel_access_token: str, project_name: str, env_name: str) -> Union[dict, bool]:
    """如果存在env_name，返回明文value的env，否则返回False"""
    headers = {"Authorization": f"Bearer {vercel_access_token}"}
    url = f"https://api.vercel.com/v9/projects/{project_name}/env/"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, verify_ssl=False) as response:
            assert response.status == 200
            content = await response.json()
            envs = content["envs"]
            for env in envs:
                if env.get("key") == env_name:
                    env_id = env.get("id")
                    url = f"https://api.vercel.com/v9/projects/{project_name}/env/{env_id}"
                    async with session.get(url, verify_ssl=False) as resp:
                        cont = await resp.json()
                        env["value"] = cont.get("value")
                        return env
            else:
                return False


async def create_or_update_env(vercel_access_token: str, project_name: str, env_name: str,
                               env_value: str):
    """
    Create or update vercel project secret.
    """
    resp = {}
    headers = {"Authorization": f"Bearer {vercel_access_token}"}
    create_env_url = f"https://api.vercel.com/v9/projects/{project_name}/env/"
    body = {
        "key": env_name,
        "value": env_value,
        "type": "encrypted",
        "target": ["production", "preview", "development"]
    }
    res = await get_env(vercel_access_token, project_name, env_name)
    async with aiohttp.ClientSession(headers=headers) as session:
        if res:
            # 存在env，更新
            env_id = res.get("id")
            url = f"https://api.vercel.com/v9/projects/{project_name}/env/{env_id}"
            async with session.post(url, verify_ssl=False, json=body) as response:
                status = response.status
                content = await response.text()
        else:
            # 创建新env
            async with session.post(create_env_url, verify_ssl=False, json=body) as response:
                status = response.status
                content = await response.text()
    if status == 200:
        resp["message"] = f"创建/更新环境变量成功"
    else:
        resp["message"] = f"创建/更新环境变量失败"
    return resp


if __name__ == '__main__':
    import asyncio

    # loop = asyncio.get_event_loop()
    # project_name = "hexo-circle-of-friends"
    # env_name = "hello"
    # env_value = "world"
    # loop.run_until_complete(create_or_update_env(vercel_access_token, project_name, env_name, env_value))
    # loop.close()
