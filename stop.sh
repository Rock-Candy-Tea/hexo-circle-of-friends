#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${RED}友链朋友圈停止脚本${NC}"
echo -e "${BLUE}=====================================${NC}"

# 1. 停止API服务
echo -e "${YELLOW}正在停止API服务...${NC}"
api_pid=$(ps aux | grep "./fcircle_api" | grep -v grep | awk '{print $2}')

if [ -z "$api_pid" ]; then
    echo -e "${BLUE}未发现正在运行的API服务${NC}"
else
    echo -e "${YELLOW}发现API服务进程ID: ${api_pid}，正在停止...${NC}"
    kill $api_pid
    sleep 2
    
    # 检查是否成功停止
    if ps -p $api_pid > /dev/null 2>&1; then
        echo -e "${RED}API服务停止失败，尝试强制终止...${NC}"
        kill -9 $api_pid
        sleep 1
    fi
    
    # 再次检查
    if ps -p $api_pid > /dev/null 2>&1; then
        echo -e "${RED}无法终止API服务，请手动终止进程ID: ${api_pid}${NC}"
    else
        echo -e "${GREEN}API服务已成功停止${NC}"
    fi
fi

# 2. 清理crontab配置
echo -e "${YELLOW}正在清理定时任务配置...${NC}"
existing_cron=$(crontab -l 2>/dev/null | grep -F "./fcircle_core")
if [ -z "$existing_cron" ]; then
    echo -e "${BLUE}未发现相关定时任务${NC}"
else
    # 删除包含./fcircle_core的行
    crontab -l 2>/dev/null | grep -v "./fcircle_core" | crontab -
    echo -e "${GREEN}成功清理定时任务${NC}"
fi

# 3. 询问是否删除数据文件
echo -e "${BLUE}=====================================${NC}"
echo -e "${YELLOW}是否需要删除数据文件?${NC}"
echo -e "${YELLOW}1. 保留所有数据${NC}"
echo -e "${YELLOW}2. 只删除日志文件 (logs/)${NC}"
echo -e "${YELLOW}3. 只删除数据库文件 (data.db)${NC}"
echo -e "${YELLOW}4. 删除所有数据 (logs/ 和 data.db)${NC}"
echo -e "${BLUE}=====================================${NC}"
read -p "请选择 [1-4] (默认: 1): " choice

case $choice in
    2)
        echo -e "${YELLOW}删除日志文件...${NC}"
        if [ -d "./logs" ]; then
            rm -rf ./logs
            echo -e "${GREEN}日志文件已删除${NC}"
        else
            echo -e "${BLUE}日志目录不存在${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}删除数据库文件...${NC}"
        if [ -f "./data.db" ]; then
            rm -f ./data.db
            echo -e "${GREEN}数据库文件已删除${NC}"
        else
            echo -e "${BLUE}数据库文件不存在${NC}"
        fi
        ;;
    4)
        echo -e "${YELLOW}删除所有数据文件...${NC}"
        if [ -d "./logs" ]; then
            rm -rf ./logs
            echo -e "${GREEN}日志文件已删除${NC}"
        else
            echo -e "${BLUE}日志目录不存在${NC}"
        fi
        
        if [ -f "./data.db" ]; then
            rm -f ./data.db
            echo -e "${GREEN}数据库文件已删除${NC}"
        else
            echo -e "${BLUE}数据库文件不存在${NC}"
        fi
        
        if [ -f "./data.json" ]; then
            rm -f ./data.json
            echo -e "${GREEN}data.json文件已删除${NC}"
        fi
        ;;
    *)
        echo -e "${BLUE}保留所有数据${NC}"
        ;;
esac

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}停止操作完成!${NC}"
echo -e "${BLUE}=====================================${NC}" 