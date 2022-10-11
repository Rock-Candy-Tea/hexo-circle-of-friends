from typing import Dict, Union
import asyncio
import aiohttp
from base64 import b64encode
from nacl import encoding, public


def get_b64encoded_data(bytes_data: bytes):
    return b64encode(bytes_data).decode("utf-8")


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


async def update(session, url, body, secret_name):
    resp = {}
    async with session.put(url, verify_ssl=False, json=body) as response:
        status = response.status
        if status == 204:
            resp["message"] = f"更新secret:{secret_name}成功"
        elif status == 201:
            resp["message"] = f"上传secret:{secret_name}成功"
        else:
            raise Exception(f"上传或更新secret:{secret_name}失败")
        resp["code"] = status
    return resp


async def create_or_update_secret(gh_access_token: str, gh_name: str, repo_name: str, secret_name: str,
                                  secret_value: str):
    """
    Create or update github repo secret.
    api: https://docs.github.com/cn/rest/actions/secrets#create-or-update-a-repository-secret,
    api: https://docs.github.com/cn/rest/actions/secrets#get-a-repository-secret
    """
    headers = {"Authorization": f"Bearer {gh_access_token}"}
    public_key_url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/secrets/public-key"
    url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/secrets/{secret_name}"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(public_key_url, verify_ssl=False) as response:
            assert response.status == 200
            content = await response.json()
            key_id = content.get("key_id")
            key = content.get("key")
            body = {"encrypted_value": encrypt(key, secret_value), "key_id": key_id}
        resp = await update(session, url, body, secret_name)
    return resp


async def bulk_create_or_update_secret(gh_access_token: str, gh_name: str, repo_name: str,
                                       secrets: Dict[str, Union[int, str]]):
    """
    Bulk create or update github repo secret.
    """
    resp = {"total": 0, "success": 0, "error": 0, "details": []}
    headers = {"Authorization": f"Bearer {gh_access_token}"}
    public_key_url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/secrets/public-key"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(public_key_url, verify_ssl=False) as response:
            assert response.status == 200, "获取github key_id失败"
            content = await response.json()
            key_id = content.get("key_id")
            key = content.get("key")
        tasks = []
        for secret_name, secret_value in secrets.items():
            body = {"encrypted_value": encrypt(key, str(secret_value)), "key_id": key_id}
            url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/secrets/{secret_name}"
            tasks.append((url, body, secret_name))
        t = [asyncio.create_task(update(session, task[0], task[1], task[2])) for task in tasks]
        resp["total"] += len(t)
        done, pending = await asyncio.wait(t)
        for d in done:
            if not d.exception() and d.result():
                resp["success"] += 1
                resp["details"].append(d.result())
            else:
                resp["error"] += 1
                resp["details"].append({"message": str(d.exception())})
    return resp


async def create_or_update_file(gh_access_token: str, gh_name: str, gh_email: str, repo_name: str, file_path: str,
                                data: str, message: str):
    """
    Create or update github repo file.
    api: https://docs.github.com/cn/rest/repos/contents#get-repository-content
    api: https://docs.github.com/cn/rest/repos/contents#create-or-update-file-contents
    """
    resp = {}
    body = {"message": message,
            "committer": {"name": gh_name, "email": gh_email},
            "content": data}
    headers = {"Authorization": f"Bearer {gh_access_token}"}
    content_url = f"https://api.github.com/repos/{gh_name}/{repo_name}/contents/{file_path}"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(content_url, verify_ssl=False) as response:
            content = await response.json()
            sha = content.get("sha")
            if sha:
                body["sha"] = sha
        async with session.put(content_url, verify_ssl=False, json=body) as response:
            # 200更新，201上传
            status = response.status
            if status == 200:
                resp["message"] = "更新文件至github成功"
            elif status == 201:
                resp["message"] = "上传文件至github成功"
            else:
                resp["message"] = "上传失败"
            resp["code"] = status
    return resp


async def crawl_now(gh_access_token: str, gh_name: str, repo_name: str):
    """
    Create a github workflow run.
    api: https://docs.github.com/cn/rest/actions/workflows#create-a-workflow-dispatch-event
    """
    resp = {}
    # ref: 运行main分支下的action
    body = {"ref": "main"}
    headers = {"Authorization": f"Bearer {gh_access_token}"}
    content_url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/workflows/main.yml/dispatches"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(content_url, verify_ssl=False, json=body) as response:
            assert response.status == 204
            if response.status != 204:
                resp["message"] = "运行失败"
                resp["code"] = 500
            else:
                resp["message"] = "运行成功"
                resp["code"] = 200
    return resp


async def check_crawler_status(gh_access_token: str, gh_name: str, repo_name: str):
    """
    Check github workflow run status.
    api: https://docs.github.com/cn/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
    """
    resp = {}
    headers = {"Authorization": f"Bearer {gh_access_token}"}
    content_url = f"https://api.github.com/repos/{gh_name}/{repo_name}/actions/runs"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(content_url, verify_ssl=False) as response:
            if response.status == 200:
                content = await response.json()
                resp["message"] = "检查运行状态成功"
                resp["code"] = 200
                # in_progress(运行中)；completed(已完成)；queued（队列中）
                status = content["workflow_runs"][0]["status"]
                if status == "in_progress" or status == "queued":
                    resp["status"] = "运行中"
                else:
                    resp["status"] = "未运行"
            else:
                resp["message"] = "检查运行状态失败"
                resp["code"] = 500
                resp["status"] = "未知"
    return resp


if __name__ == '__main__':
    # import asyncio
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(create_or_update_file(gh_access_token, gh_name, gh_email, repo_name, b64encoded_data))
    # loop.close()
    pass
