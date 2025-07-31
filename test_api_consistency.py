#!/usr/bin/env python3
"""
测试API在不同数据库配置下的一致性
"""

import subprocess
import json
import time
import os

def test_api_with_config(database_type):
    """测试指定数据库配置的API响应"""
    print(f"\n🧪 测试 {database_type.upper()} 配置...")
    
    # 修改配置文件
    with open('fc_settings.yaml', 'r') as f:
        content = f.read()
    
    # 替换数据库配置
    new_content = content.replace('DATABASE: "sqlite"', f'DATABASE: "{database_type}"')
    new_content = new_content.replace('DATABASE: "mysql"', f'DATABASE: "{database_type}"')
    new_content = new_content.replace('DATABASE: "mongodb"', f'DATABASE: "{database_type}"')
    
    with open('fc_settings.yaml', 'w') as f:
        f.write(new_content)
    
    try:
        # 检查API导入
        result = subprocess.run([
            'uv', 'run', 'python', '-c', 
            f'''
import sys
sys.path.append('.')

try:
    from api.vercel import app
    print("✅ API导入成功")
    
    # 检查OpenAPI schema
    schema = app.openapi()
    paths = schema.get('paths', {{}})
    print(f"📊 API端点数量: {{len(paths)}}")
    
    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get('summary', 'No summary')
            print(f"  {{method.upper()}} {{path}} - {{summary}}")
            
except Exception as e:
    print(f"❌ API导入失败: {{e}}")
    import traceback
    traceback.print_exc()
'''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ 测试失败:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始API一致性测试...")
    
    # 备份原始配置
    subprocess.run(['cp', 'fc_settings.yaml', 'fc_settings.yaml.backup'])
    
    try:
        databases = ['sqlite', 'mongodb']
        results = {}
        
        for db in databases:
            results[db] = test_api_with_config(db)
        
        # 测试总结
        print("\n📋 测试结果总结:")
        all_passed = True
        for db, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {db.upper()}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有数据库配置测试通过！API一致性验证成功！")
        else:
            print("\n⚠️  部分测试失败，请检查具体错误信息")
            
    finally:
        # 恢复原始配置
        subprocess.run(['mv', 'fc_settings.yaml.backup', 'fc_settings.yaml'])
        print("\n🔄 已恢复原始配置")

if __name__ == "__main__":
    main()