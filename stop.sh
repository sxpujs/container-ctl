#!/bin/bash

# 检查 app.pid 是否存在
if [ ! -f ./app.pid ]; then
    echo "Error: app.pid 文件不存在，应用可能未运行。"
    exit 1
fi

# 读取 PID
PID=$(cat ./app.pid)

# 检查 PID 是否有效
if ps -p $PID > /dev/null 2>&1; then
    echo "正在停止进程 $PID ..."
    kill $PID
    sleep 2  # 等待进程结束
    if ps -p $PID > /dev/null 2>&1; then
        echo "进程 $PID 未能正常停止，尝试强制结束..."
        kill -9 $PID
    fi
    echo "进程 $PID 已停止。"
else
    echo "进程 $PID 不存在，可能已停止。"
fi

# 删除 app.pid 文件
rm -f ./app.pid
echo "已删除 app.pid 文件。"

exit 0