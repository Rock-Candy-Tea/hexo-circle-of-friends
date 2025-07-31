#!/usr/bin/env python3
"""
版本号更新工具

自动更新项目中的版本号，包括：
1. Cargo.toml workspace 版本
2. pyproject.toml 版本
3. FastAPI 应用版本
4. 重新生成 Swagger 文档

用法:
  python update_version.py 6.1.0        # 更新到指定版本
  python update_version.py --bump patch # 自动递增补丁版本
  python update_version.py --bump minor # 自动递增次版本
  python update_version.py --bump major # 自动递增主版本
"""

import argparse
import re
import subprocess
from pathlib import Path


class VersionUpdater:
    def __init__(self):
        self.root_path = Path(__file__).parent  # 脚本现在在根目录
        self.cargo_toml = self.root_path / "Cargo.toml"
        self.pyproject_toml = self.root_path / "pyproject.toml"
        self.vercel_py = self.root_path / "api" / "vercel.py"
        self.swagger_json = self.root_path / "api" / "swagger.json"

    def get_current_version(self):
        """从 Cargo.toml workspace 获取当前版本"""
        with open(self.cargo_toml, "r") as f:
            content = f.read()

        # 查找 [workspace.package] 下的 version
        workspace_match = re.search(r"\[workspace\.package\]", content)
        if workspace_match:
            workspace_section = content[workspace_match.end() :]
            next_section = re.search(r"\n\[", workspace_section)
            if next_section:
                workspace_section = workspace_section[: next_section.start()]

            version_match = re.search(r'version\s*=\s*"([^"]+)"', workspace_section)
            if version_match:
                return version_match.group(1)

        raise ValueError("无法在 Cargo.toml 中找到当前版本")

    def bump_version(self, current_version, bump_type):
        """递增版本号"""
        parts = current_version.split(".")
        if len(parts) < 3:
            parts.extend(["0"] * (3 - len(parts)))

        major, minor, patch = map(int, parts[:3])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"无效的递增类型: {bump_type}")

        return f"{major}.{minor}.{patch}"

    def update_cargo_version(self, new_version):
        """更新 Cargo.toml workspace 版本"""
        print(f"📝 更新 Cargo.toml 版本: {new_version}")

        with open(self.cargo_toml, "r") as f:
            content = f.read()

        # 替换 [workspace.package] 下的版本
        pattern = r'(\[workspace\.package\][\s\S]*?version\s*=\s*)"[^"]+"'
        replacement = r'\1"' + new_version + '"'
        new_content = re.sub(pattern, replacement, content)

        if new_content == content:
            print("⚠️  Cargo.toml 版本未改变")
            return False

        with open(self.cargo_toml, "w") as f:
            f.write(new_content)

        print("✅ Cargo.toml 版本更新完成")
        return True

    def update_pyproject_version(self, new_version):
        """更新 pyproject.toml 版本"""
        print(f"📝 更新 pyproject.toml 版本: {new_version}")

        with open(self.pyproject_toml, "r") as f:
            content = f.read()

        # 替换版本号
        pattern = r'(version\s*=\s*)"[^"]+"'
        replacement = r'\1"' + new_version + '"'
        new_content = re.sub(pattern, replacement, content)

        if new_content == content:
            print("⚠️  pyproject.toml 版本未改变")
            return False

        with open(self.pyproject_toml, "w") as f:
            f.write(new_content)

        print("✅ pyproject.toml 版本更新完成")
        return True

    def update_fastapi_version(self, new_version):
        """更新 FastAPI 应用版本"""
        print(f"📝 更新 FastAPI 应用版本: {new_version}")

        with open(self.vercel_py, "r") as f:
            content = f.read()

        # 替换 FastAPI 应用的版本
        pattern = r'(version\s*=\s*)"[^"]+"'
        replacement = r'\1"' + new_version + '"'
        new_content = re.sub(pattern, replacement, content)

        if new_content == content:
            print("⚠️  FastAPI 应用版本未改变")
            return False

        with open(self.vercel_py, "w") as f:
            f.write(new_content)

        print("✅ FastAPI 应用版本更新完成")
        return True

    def update_swagger_docs(self):
        """重新生成 Swagger 文档"""
        print("📚 重新生成 Swagger 文档")

        try:
            # 生成新的 Swagger 文档
            cmd = [
                "uv",
                "run",
                "python",
                "-c",
                """
import sys
import os
sys.path.append('.')
from api.vercel import app
import json

openapi_schema = app.openapi()
with open('api/swagger.json', 'w', encoding='utf-8') as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
print("✅ Swagger文档已更新")
                """,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.root_path
            )

            if result.returncode == 0:
                print("✅ Swagger 文档生成成功")
                return True
            else:
                print(f"❌ Swagger 文档生成失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Swagger 文档生成异常: {e}")
            return False

    def validate_version(self, new_version):
        """验证所有文件中的版本是否一致"""
        print("🔍 验证版本一致性")

        versions = {}

        # 检查 Cargo.toml
        try:
            versions["Cargo.toml"] = self.get_current_version()
        except Exception as e:
            print(f"⚠️  无法读取 Cargo.toml 版本: {e}")

        # 检查 pyproject.toml
        try:
            with open(self.pyproject_toml, "r") as f:
                content = f.read()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    versions["pyproject.toml"] = match.group(1)
        except Exception as e:
            print(f"⚠️  无法读取 pyproject.toml 版本: {e}")

        # 检查 FastAPI 版本
        try:
            with open(self.vercel_py, "r") as f:
                content = f.read()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    versions["FastAPI"] = match.group(1)
        except Exception as e:
            print(f"⚠️  无法读取 FastAPI 版本: {e}")

        # 显示版本信息
        print("📋 当前版本信息:")
        for source, version in versions.items():
            status = "✅" if version == new_version else "❌"
            print(f"  {source}: {version} {status}")

        # 检查一致性
        all_versions = set(versions.values())
        if len(all_versions) == 1 and new_version in all_versions:
            print("✅ 所有版本号一致")
            return True
        else:
            print("❌ 版本号不一致")
            return False

    def update_version(self, new_version):
        """更新所有文件的版本号"""
        current_version = self.get_current_version()
        print(f"🎯 当前版本: {current_version}")
        print(f"🎯 目标版本: {new_version}")

        # if current_version == new_version:
        #     print("⚠️  版本号相同，无需更新")
        #     return True

        print("\n🚀 开始更新版本号...")

        # 更新各个文件
        updated_files = []

        if self.update_cargo_version(new_version):
            updated_files.append("Cargo.toml")

        if self.update_pyproject_version(new_version):
            updated_files.append("pyproject.toml")

        if self.update_fastapi_version(new_version):
            updated_files.append("FastAPI应用")

        # 重新生成 Swagger 文档
        if self.update_swagger_docs():
            updated_files.append("Swagger文档")

        # 验证版本一致性
        if not self.validate_version(new_version):
            print("❌ 版本验证失败")
            return False

        print("\n🎉 版本更新完成！")
        print(f"📦 新版本: {new_version}")
        print(f"📁 更新的文件: {', '.join(updated_files)}")
        print("\n💡 注意:")
        print(f"  - Git 标签应使用: v{new_version}")
        print(f"  - API 版本显示: {new_version} (不带v前缀)")

        return True


def main():
    parser = argparse.ArgumentParser(description="版本号更新工具")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("version", nargs="?", help="指定版本号")
    group.add_argument(
        "--bump", choices=["major", "minor", "patch"], help="自动递增版本号"
    )

    args = parser.parse_args()

    updater = VersionUpdater()

    try:
        if args.version:
            new_version = args.version
        else:
            current_version = updater.get_current_version()
            new_version = updater.bump_version(current_version, args.bump)

        # 验证版本格式
        if not re.match(r"^\d+\.\d+\.\d+", new_version):
            print(f"❌ 无效的版本格式: {new_version}")
            return 1

        success = updater.update_version(new_version)
        return 0 if success else 1

    except Exception as e:
        print(f"❌ 版本更新失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
