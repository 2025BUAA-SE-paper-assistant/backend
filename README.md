# Epp-BackEnd

## 注意

本地开发的时候需要将setting.py里面的SESSION_COOKIE_SECURE设置成False

## 向量库设计

使用Milvus, 维度**768**, 账号密码在backend/vector_database/doc内, 已实现插入和检索

## 新建虚拟环境

1. 确保已安装 `virtualenv`，如果未安装，请运行以下命令安装：
   ```bash
   pip install virtualenv
   ```

2. 在项目目录下创建虚拟环境：
   ```bash
   virtualenv myenv
   ```

3. 激活虚拟环境：
   - Linux/macOS:
     ```bash
     source myenv/bin/activate
     ```
   - Windows:
     ```bash
     myenv\Scripts\activate
     ```

4. 安装项目依赖：
   ```bash
   pip install -r requirements.txt
   ```

tmux new -s my_terminal

source myenv/bin/activate  # 激活虚拟环境


export PYTHONPATH=$PYTHONPATH:/root/nbackend

python manage.py runserver 0.0.0.0:8010 > output.txt

tmux attach -t my_terminal  # 恢复会话


进入服务
sudo mysql -u root -p

创建数据库
CREATE DATABASE eppdb;
USE eppdb;

mysql -u root -p eppdb < /root/nbackend/2024_EPP.sql
