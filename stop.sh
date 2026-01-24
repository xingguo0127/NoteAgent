#!/bin/bash

###############################################################################
# ObsAgent 停止脚本
# 用法: ./stop.sh [--force]
###############################################################################

# 配置
PID_FILE=".pid"
DEFAULT_PORT=8080

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 解析命令行参数
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--force]"
            exit 1
            ;;
    esac
done

# 停止进程函数
stop_process() {
    local PID=$1
    local NAME=$2

    echo "🛑 正在停止 $NAME (PID: $PID)..."

    # 先尝试优雅终止
    kill $PID 2>/dev/null
    sleep 2

    # 检查是否还在运行
    if ps -p $PID > /dev/null 2>&1; then
        if [ "$FORCE" = true ]; then
            echo "⚠️  进程未响应，强制终止..."
            kill -9 $PID 2>/dev/null
            sleep 1
        else
            echo "⚠️  进程未响应，使用 --force 强制终止"
            return 1
        fi
    fi

    # 最终检查
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ 无法停止进程"
        return 1
    else
        echo "✅ $NAME 已停止"
        return 0
    fi
}

# 主逻辑
STOPPED=false

# 方式1: 通过 PID 文件停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        if stop_process $PID "ObsAgent"; then
            STOPPED=true
        fi
    else
        echo "⚠️  PID 文件存在但进程不存在，清理残留文件..."
    fi
    rm -f "$PID_FILE"
fi

# 方式2: 如果 PID 文件不存在，尝试通过端口查找
if [ "$STOPPED" = false ]; then
    PID=$(lsof -ti :$DEFAULT_PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "📍 通过端口 $DEFAULT_PORT 找到进程..."
        if stop_process $PID "ObsAgent"; then
            STOPPED=true
        fi
    fi
fi

# 结果输出
if [ "$STOPPED" = false ]; then
    echo "ℹ️  ObsAgent 未在运行"
fi
