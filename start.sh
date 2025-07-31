#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}友链朋友圈安装脚本${NC}"
echo -e "${BLUE}=====================================${NC}"

# 1. 交互式询问用户博客友链页URL
echo -e "${YELLOW}请输入您的博客友链页URL (默认: https://www.yyyzyyyz.cn/link/)${NC}"
read -p "> " blog_url

# 如果用户没有输入，使用默认值
if [ -z "$blog_url" ]; then
    blog_url="https://www.yyyzyyyz.cn/link/"
    echo -e "${BLUE}使用默认URL: ${blog_url}${NC}"
else
    echo -e "${GREEN}使用URL: ${blog_url}${NC}"
fi

# 2. 交互式询问API服务端口
echo -e "${YELLOW}请输入API服务监听端口 (默认: 8000)${NC}"
read -p "> " api_port

# 端口验证函数
validate_port() {
    local port=$1
    if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
        return 0
    else
        return 1
    fi
}

# 如果用户没有输入，使用默认值
if [ -z "$api_port" ]; then
    api_port="8000"
    echo -e "${BLUE}使用默认端口: ${api_port}${NC}"
else
    # 验证端口号
    if validate_port "$api_port"; then
        echo -e "${GREEN}使用端口: ${api_port}${NC}"
    else
        echo -e "${RED}无效的端口号: ${api_port}，使用默认端口: 8000${NC}"
        api_port="8000"
    fi
fi

# 更新fc_settings.yaml文件
sed -i.bak "s|https://www.yyyzyyyz.cn/link/|${blog_url}|" fc_settings.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}成功更新配置文件${NC}"
else
    echo -e "${RED}更新配置文件失败${NC}"
    exit 1
fi

# 3. 从fc_settings.yaml获取CRON表达式
cron_expr=$(grep "CRON:" fc_settings.yaml | cut -d'"' -f2)
if [ -z "$cron_expr" ]; then
    echo -e "${RED}无法从配置文件中获取CRON表达式${NC}"
    exit 1
else
    echo -e "${GREEN}获取到CRON表达式: ${cron_expr}${NC}"
fi

# 4. 从GitHub release下载二进制程序（占位）
echo -e "${YELLOW}检查二进制程序...${NC}"
# TODO: 从GitHub release下载二进制程序
# 示例代码:
# latest_release=$(curl -s https://api.github.com/repos/username/repo/releases/latest | grep "tag_name" | cut -d'"' -f4)
# curl -L https://github.com/username/repo/releases/download/${latest_release}/core -o core
# curl -L https://github.com/username/repo/releases/download/${latest_release}/api -o api

# 检查二进制文件是否存在
if [ ! -f "./fcircle_core" ] || [ ! -f "./fcircle_api" ]; then
    echo -e "${RED}错误: 找不到二进制文件 fcircle_core 或 fcircle_api${NC}"
    exit 1
fi

# 确保二进制文件有执行权限
chmod +x ./fcircle_core
chmod +x ./fcircle_api

# 5. 设置定时任务并立即运行core
echo -e "${YELLOW}设置定时任务...${NC}"
# 检查是否已存在相同的定时任务
existing_cron=$(crontab -l 2>/dev/null | grep -F "./fcircle_core")
if [ -z "$existing_cron" ]; then
    # 添加到crontab，不重定向输出
    (crontab -l 2>/dev/null; echo "$cron_expr cd $(pwd) && ./fcircle_core") | crontab -
    echo -e "${GREEN}成功添加定时任务${NC}"
else
    echo -e "${BLUE}定时任务已存在，跳过添加${NC}"
fi

# 6. 先启动API服务，使用用户指定的端口
echo -e "${YELLOW}启动API服务在端口 ${api_port}...${NC}"
nohup ./fcircle_api -p "$api_port" >/dev/null 2>&1 &
api_pid=$!

# 等待一下确认API是否成功启动
sleep 2
if ps -p $api_pid > /dev/null; then
    echo -e "${GREEN}API服务成功启动，端口: ${api_port}，PID: ${api_pid}${NC}"
else
    echo -e "${RED}API服务启动失败，请检查日志${NC}"
    exit 1
fi

# 首次运行fcircle_core（后台执行）
echo -e "${YELLOW}后台运行首次fcircle_core任务...${NC}"
mkdir -p logs
nohup ./fcircle_core >/dev/null 2>&1 &
core_pid=$!
echo -e "${GREEN}fcircle_core已启动后台运行，PID: ${core_pid}${NC}"

# 7. 输出提示信息
echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}安装完成!${NC}"
echo -e "${YELLOW}提示:${NC}"
echo -e "- 运行日志位于 ./logs/ 目录"
echo -e "- API服务地址: http://localhost:${api_port}"
echo -e "- API服务进程ID: ${api_pid}"
echo -e "- 首次fcircle_core任务进程ID: ${core_pid}"
echo -e "- 检查服务状态: ps -p ${api_pid} ${core_pid}"
echo -e "- 停止API服务: kill ${api_pid}"
echo -e "- 停止fcircle_core任务: kill ${core_pid}"
echo -e "- 定时任务已设置为: ${cron_expr}"
echo -e "- 查看定时任务: crontab -l"
echo -e "${BLUE}=====================================${NC}"
