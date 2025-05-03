#!/bin/bash

if [ -f ./app.pid ]; then
    PID=$(cat ./app.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "应用已在运行 (PID: $PID)，无需重复启动。"
        exit 1
    else
        echo "检测到过时的 PID 文件，删除后重新启动应用..."
        rm -f ./app.pid
    fi
fi

# 使用 `setsid` 启动 Python 进程，使其独立于当前 Shell
setsid python3 src/app.py > ./app.log 2>&1 & echo $! > ./app.pid

PID=$(cat ./app.pid)
echo "应用已启动，进程 ID: $PID"

# 显示日志
echo "正在实时查看日志 (Ctrl+C 退出查看，程序继续运行)："
tail -f ./app.log