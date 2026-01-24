#!/bin/bash

###############################################################################
# ObsAgent 启动脚本
# 用法: ./start.sh [--port PORT] [--host HOST]
###############################################################################

# 默认配置
DEFAULT_PORT=8080
DEFAULT_HOST="0.0.0.0"
CONDA_ENV="base"
PID_FILE=".pid"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/server.log"

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 解析命令行参数
PORT=$DEFAULT_PORT
HOST=$DEFAULT_HOST

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--port PORT] [--host HOST]"
            exit 1
            ;;
    esac
done

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "❌ ObsAgent 已经在运行中 (PID: $OLD_PID)"
        echo "如需重启，请先运行: ./stop.sh"
        exit 1
    else
        echo "⚠️  发现残留 PID 文件，正在清理..."
        rm -f "$PID_FILE"
    fi
fi

# 创建日志目录
mkdir -p "$LOG_DIR"

# 初始化 conda
echo "🔧 初始化 Conda 环境..."
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 激活 conda 环境
echo "🐍 激活 Conda 环境: $CONDA_ENV"
conda activate "$CONDA_ENV"

if [ $? -ne 0 ]; then
    echo "❌ 无法激活 Conda 环境: $CONDA_ENV"
    echo "请确认环境是否存在: conda env list"
    exit 1
fi

# 检查 Python 和依赖
echo "✅ 检查 Python 环境..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python 未正确安装"
    exit 1
fi

# 启动服务
echo "🚀 启动 ObsAgent 服务..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   日志: $LOG_FILE"

nohup python -m obs_agent --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
PID=$!

# 保存 PID
echo $PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查进程是否还在运行
if ps -p $PID > /dev/null; then
    echo "✅ ObsAgent 启动成功!"
    echo "   PID: $PID"
    echo "   访问地址: http://$HOST:$PORT"
    echo "   日志文件: $LOG_FILE"
    echo ""
    echo "💡 管理命令:"
    echo "   查看日志: tail -f $LOG_FILE"
    echo "   停止服务: ./stop.sh"
else
    echo "❌ 服务启动失败，请检查日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
