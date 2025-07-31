# -*- coding:utf-8 -*-
# Author：yyyz
import yaml
import os


def get_base_path():
    base_path = os.environ.get(
        "BASE_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    # assert base_path, "Environment variable 'BASE_PATH' is not detected," \
    #                   f"make sure it is added! {os.getcwd()},,{sys.argv[0]}"
    return base_path


def get_user_settings():
    """
    加载用户配置文件
    :return:
    """
    base_path = get_base_path()
    path = os.path.join(base_path, "fc_settings.yaml")
    try:
        print("读取配置文件...")
        f = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        print("读取配置文件失败！请检查用户配置文件是否正确！")
        raise IOError
    try:
        user_conf = yaml.safe_load(f)
    except Exception as e:
        print(e)
        print("读取配置文件失败，请检查配置文件内容语法是否正确！")
        raise IOError
    print("成功获取用户配置！")
    f.close()
    return user_conf


def is_vercel_sqlite():
    settings = get_user_settings()
    return os.environ.get("VERCEL") and settings["DATABASE"] == "sqlite"


def is_vercel():
    return os.environ.get("VERCEL")


# 版本管理模块 - 整合自 version_manager.py
def get_version():
    """
    获取当前版本信息

    Returns:
        dict: 包含版本号的字典
    """
    # 优先从环境变量获取
    version = os.getenv("VERSION")

    if not version:
        # 尝试从 pyproject.toml 读取
        try:
            pyproject_path = os.path.join(get_base_path(), "pyproject.toml")
            if os.path.exists(pyproject_path):
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 简单解析 version 行
                    for line in content.split("\n"):
                        if line.strip().startswith("version ="):
                            version = line.split("=")[1].strip().strip('"')
                            break
        except Exception:
            pass

    # 尝试从 Cargo workspace 根目录的 Cargo.toml 读取
    if not version:
        try:
            cargo_toml = os.path.join(get_base_path(), "Cargo.toml")
            if os.path.exists(cargo_toml):
                with open(cargo_toml, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 查找 [workspace.package] 下的 version
                    in_workspace_package = False
                    for line in content.split("\n"):
                        if line.strip() == "[workspace.package]":
                            in_workspace_package = True
                        elif line.strip().startswith("[") and in_workspace_package:
                            break
                        elif in_workspace_package and line.strip().startswith(
                            "version ="
                        ):
                            version = line.split("=")[1].strip().strip('"')
                            break
        except Exception:
            pass

    # 默认版本
    if not version:
        version = "1.0.0"

    return {"version": version}


if __name__ == "__main__":
    print(get_user_settings())
