#!/bin/bash
# ObsAgent 启动脚本

cd "$(dirname "$0")"

# 激活 conda 环境
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate base

# 检查是否已运行
if [ -f .pid ]; then
    PID=$(cat .pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "ObsAgent 已在运行 (PID: $PID)"
        exit 1
    fi
fi

# 启动服务
echo "正在启动 ObsAgent..."
nohup python -m obs_agent > logs/server.log 2>&1 &
PID=$!
echo $PID > .pid

sleep 2

# 检查是否启动成功
if ps -p $PID > /dev/null 2>&1; then
    echo "ObsAgent 启动成功 (PID: $PID)"
    echo "日志文件: logs/server.log"
    echo "访问地址: http://localhost:8080"
else
    echo "ObsAgent 启动失败，请查看日志"
    rm -f .pid
    exit 1
fi
