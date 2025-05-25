# 检查 tmux 会话是否存在，如果不存在则创建
tmux has-session -t my_terminal 2>/dev/null || tmux new-session -d -s my_terminal

source .venv/bin/activate

cd backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# 启动定时任务
python manage.py crontab remove  # 移除旧任务
python manage.py crontab add     # 添加新任务
python manage.py crontab show    # 验证任务列表

# 停止现有的 uvicorn 进程（无需 sudo）
pkill -f "uvicorn backend.asgi:application" || true

# 启动 uvicorn
uvicorn backend.asgi:application --host 0.0.0.0 --port 8010 --reload

