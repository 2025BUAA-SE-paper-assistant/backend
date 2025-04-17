# 检查 tmux 会话是否存在，如果不存在则创建
tmux has-session -t my_terminal 2>/dev/null || tmux new-session -d -s my_terminal

cd backend
source myenv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# 停止现有的 runserver 进程（无需 sudo）
pkill -f "python manage.py runserver" || true

# 启动 runserver
python manage.py runserver 0.0.0.0:8010

