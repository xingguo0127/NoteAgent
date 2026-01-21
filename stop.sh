#!/bin/bash
# ObsAgent 停止脚本

cd "$(dirname "$0")"

if [ -f .pid ]; then
    PID=$(cat .pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止 ObsAgent (PID: $PID)..."
        kill $PID
        sleep 2

        # 如果还在运行，强制终止
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制终止..."
            kill -9 $PID
        fi

        rm -f .pid
        echo "ObsAgent 已停止"
    else
        echo "ObsAgent 未在运行"
        rm -f .pid
    fi
else
    # 尝试通过端口查找进程
    PID=$(lsof -ti :8080 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "正在停止 ObsAgent (PID: $PID)..."
        kill $PID
        sleep 2
        echo "ObsAgent 已停止"
    else
        echo "ObsAgent 未在运行"
    fi
fi
