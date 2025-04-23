#!/bin/bash

# 获取当前所有OpenVPN连接的进程ID
pid=$(pgrep -f openvpn)

# 如果找到了进程ID，则执行以下操作
if [ ! -z "$pid" ]; then
    # 逐一终止OpenVPN进程
    for p in $pid; do
        kill $p
    done
    echo "OpenVPN连接已关闭。"
else
    echo "未找到OpenVPN连接。"
fi