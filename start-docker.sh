#!/usr/bin/env bash

echo "1/4 拉取最新的镜像"
docker pull python:3.12-slim

echo "2/4 停止旧容器"
docker stop cabinet-sandbox

echo "3/4 删除旧容器"
docker rm cabinet-sandbox

echo "4/4 启动新容器"
docker run -it --name cabinet-sandbox python:3.12-slim bash

# 输出容器进程
docker ps

# 输出日志
docker logs -f cabinet-sandbox